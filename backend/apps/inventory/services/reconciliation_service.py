"""
Services for inventory reconciliation and report workflows.
"""
from __future__ import annotations

import csv
from io import BytesIO, StringIO
from typing import Any, Dict, Iterable, List
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.services.base_crud import BaseCRUDService
from apps.inventory.models import (
    InventoryDifference,
    InventoryReconciliation,
    InventoryReport,
    InventoryTask,
)


def _user_display_name(user) -> str:
    """Return the best available display name for a user instance."""
    if not user:
        return ''
    return user.get_full_name() or user.username or user.email or str(user.id)


class InventoryReconciliationService(BaseCRUDService):
    """Service layer for inventory reconciliation records."""

    def __init__(self):
        super().__init__(InventoryReconciliation)

    def create_reconciliation(
        self,
        *,
        task_id: str,
        user,
        note: str = '',
    ) -> InventoryReconciliation:
        """Create a reconciliation record from a completed inventory task."""
        task = InventoryTask.objects.get(id=task_id, is_deleted=False)
        self._validate_task_for_reconciliation(task)

        existing = InventoryReconciliation.objects.filter(
            task_id=task.id,
            is_deleted=False,
        ).exclude(
            status=InventoryReconciliation.STATUS_REJECTED,
        ).first()
        if existing is not None:
            raise ValidationError(_('A reconciliation already exists for this task.'))

        metrics = self._build_reconciliation_metrics(task)
        return InventoryReconciliation.objects.create(
            task=task,
            normal_count=metrics['normal_count'],
            abnormal_count=metrics['abnormal_count'],
            difference_count=metrics['difference_count'],
            adjustment_count=metrics['adjustment_count'],
            adjustments=metrics['adjustments'],
            note=note.strip(),
            status=InventoryReconciliation.STATUS_DRAFT,
            reconciled_at=timezone.now(),
            reconciled_by=user,
            current_approver=task.created_by,
            organization_id=task.organization_id,
            created_by=user,
        )

    def submit(self, reconciliation_id: str, user) -> InventoryReconciliation:
        """Submit a draft reconciliation for approval."""
        reconciliation = self.get(
            reconciliation_id,
            organization_id=user.organization_id,
            user=user,
        )
        if reconciliation.status not in {
            InventoryReconciliation.STATUS_DRAFT,
            InventoryReconciliation.STATUS_REJECTED,
        }:
            raise ValidationError(_('Only draft or rejected reconciliations can be submitted.'))

        reconciliation.status = InventoryReconciliation.STATUS_SUBMITTED
        reconciliation.submitted_at = timezone.now()
        reconciliation.rejected_at = None
        reconciliation.current_approver = reconciliation.task.created_by
        reconciliation.save(
            update_fields=['status', 'submitted_at', 'rejected_at', 'current_approver', 'updated_at']
        )
        return reconciliation

    def approve(
        self,
        reconciliation_id: str,
        *,
        user,
        comment: str = '',
    ) -> InventoryReconciliation:
        """Approve a submitted reconciliation."""
        reconciliation = self.get(
            reconciliation_id,
            organization_id=user.organization_id,
            user=user,
        )
        if reconciliation.status != InventoryReconciliation.STATUS_SUBMITTED:
            raise ValidationError(_('Only submitted reconciliations can be approved.'))

        reconciliation.status = InventoryReconciliation.STATUS_APPROVED
        reconciliation.approved_at = timezone.now()
        reconciliation.current_approver = None
        reconciliation.note = self._append_note(reconciliation.note, comment)
        reconciliation.save(
            update_fields=['status', 'approved_at', 'current_approver', 'note', 'updated_at']
        )
        return reconciliation

    def reject(
        self,
        reconciliation_id: str,
        *,
        user,
        reason: str = '',
    ) -> InventoryReconciliation:
        """Reject a submitted reconciliation."""
        reconciliation = self.get(
            reconciliation_id,
            organization_id=user.organization_id,
            user=user,
        )
        if reconciliation.status != InventoryReconciliation.STATUS_SUBMITTED:
            raise ValidationError(_('Only submitted reconciliations can be rejected.'))

        reconciliation.status = InventoryReconciliation.STATUS_REJECTED
        reconciliation.rejected_at = timezone.now()
        reconciliation.current_approver = None
        reconciliation.note = self._append_note(reconciliation.note, reason)
        reconciliation.save(
            update_fields=['status', 'rejected_at', 'current_approver', 'note', 'updated_at']
        )
        return reconciliation

    @staticmethod
    def _validate_task_for_reconciliation(task: InventoryTask) -> None:
        """Ensure the task is ready for reconciliation."""
        if task.status != InventoryTask.STATUS_COMPLETED:
            raise ValidationError(_('Only completed inventory tasks can be reconciled.'))

    def _build_reconciliation_metrics(self, task: InventoryTask) -> Dict[str, Any]:
        """Build normalized reconciliation metrics for a task."""
        differences = list(
            InventoryDifference.objects.filter(
                task_id=task.id,
                is_deleted=False,
            ).select_related('asset')
        )
        adjustments = [
            {
                'difference_id': str(diff.id),
                'difference_type': diff.difference_type,
                'difference_type_label': str(diff.get_difference_type_display()),
                'asset_id': str(diff.asset_id) if diff.asset_id else '',
                'asset_code': getattr(diff.asset, 'asset_code', ''),
                'asset_name': getattr(diff.asset, 'asset_name', ''),
                'status': diff.status,
                'status_label': str(diff.get_status_display()),
                'resolution': diff.resolution,
                'closure_type': diff.closure_type,
                'resolved_at': diff.resolved_at.isoformat() if diff.resolved_at else None,
            }
            for diff in differences
            if diff.status != InventoryDifference.STATUS_PENDING
        ]
        difference_count = len(differences)

        return {
            'normal_count': int(task.normal_count or 0),
            'abnormal_count': difference_count,
            'difference_count': difference_count,
            'adjustment_count': len(adjustments),
            'adjustments': adjustments,
        }

    @staticmethod
    def _append_note(existing_note: str, extra_note: str) -> str:
        """Append an optional note with a newline separator."""
        normalized_note = str(extra_note or '').strip()
        if not normalized_note:
            return existing_note or ''
        if not existing_note:
            return normalized_note
        return f"{existing_note.rstrip()}\n{normalized_note}"


class InventoryReportService(BaseCRUDService):
    """Service layer for generated inventory reports."""

    def __init__(self):
        super().__init__(InventoryReport)

    @transaction.atomic
    def generate_report(
        self,
        *,
        task_id: str,
        user,
        template_id: str = '',
    ) -> InventoryReport:
        """Generate an inventory report snapshot from task and difference data."""
        task = InventoryTask.objects.get(id=task_id, is_deleted=False)
        self._validate_task_for_report(task)

        report_payload = self._build_report_payload(task)
        return InventoryReport.objects.create(
            task=task,
            template_id=template_id.strip(),
            status=InventoryReport.STATUS_DRAFT,
            summary=report_payload['summary'],
            report_data=report_payload['report_data'],
            approvals=[],
            generated_by=user,
            generated_at=timezone.now(),
            current_approver=task.created_by,
            organization_id=task.organization_id,
            created_by=user,
        )

    def submit(self, report_id: str, user) -> InventoryReport:
        """Submit an inventory report for approval."""
        report = self.get(report_id, organization_id=user.organization_id, user=user)
        if report.status not in {
            InventoryReport.STATUS_DRAFT,
            InventoryReport.STATUS_REJECTED,
        }:
            raise ValidationError(_('Only draft or rejected reports can be submitted.'))

        approvals = list(report.approvals or [])
        approvals.append(
            {
                'level': len(approvals) + 1,
                'approver': {
                    'id': str(user.id),
                    'username': user.username,
                    'full_name': _user_display_name(user),
                },
                'action': 'submit',
                'approved_at': timezone.now().isoformat(),
            }
        )
        report.status = InventoryReport.STATUS_PENDING_APPROVAL
        report.submitted_at = timezone.now()
        report.rejected_at = None
        report.current_approver = report.task.created_by
        report.approvals = approvals
        report.save(
            update_fields=[
                'status',
                'submitted_at',
                'rejected_at',
                'current_approver',
                'approvals',
                'updated_at',
            ]
        )
        return report

    def approve(self, report_id: str, *, user, opinion: str = '') -> InventoryReport:
        """Approve a submitted inventory report."""
        report = self.get(report_id, organization_id=user.organization_id, user=user)
        if report.status != InventoryReport.STATUS_PENDING_APPROVAL:
            raise ValidationError(_('Only pending reports can be approved.'))

        approvals = list(report.approvals or [])
        approvals.append(
            {
                'level': len(approvals) + 1,
                'approver': {
                    'id': str(user.id),
                    'username': user.username,
                    'full_name': _user_display_name(user),
                },
                'action': 'approve',
                'opinion': opinion.strip(),
                'approved_at': timezone.now().isoformat(),
            }
        )
        report.status = InventoryReport.STATUS_APPROVED
        report.approved_at = timezone.now()
        report.current_approver = None
        report.approvals = approvals
        report.save(
            update_fields=['status', 'approved_at', 'current_approver', 'approvals', 'updated_at']
        )
        return report

    def reject(self, report_id: str, *, user, opinion: str = '') -> InventoryReport:
        """Reject a submitted inventory report."""
        report = self.get(report_id, organization_id=user.organization_id, user=user)
        if report.status != InventoryReport.STATUS_PENDING_APPROVAL:
            raise ValidationError(_('Only pending reports can be rejected.'))

        approvals = list(report.approvals or [])
        approvals.append(
            {
                'level': len(approvals) + 1,
                'approver': {
                    'id': str(user.id),
                    'username': user.username,
                    'full_name': _user_display_name(user),
                },
                'action': 'reject',
                'opinion': opinion.strip(),
                'approved_at': timezone.now().isoformat(),
            }
        )
        report.status = InventoryReport.STATUS_REJECTED
        report.rejected_at = timezone.now()
        report.current_approver = None
        report.approvals = approvals
        report.save(
            update_fields=['status', 'rejected_at', 'current_approver', 'approvals', 'updated_at']
        )
        return report

    def export_report(self, report_id: str, *, user, file_format: str = 'pdf') -> HttpResponse:
        """Export a report as PDF, XLSX, or CSV."""
        report = self.get(report_id, organization_id=user.organization_id, user=user)
        normalized_format = (file_format or 'pdf').strip().lower()
        if normalized_format == 'excel':
            normalized_format = 'xlsx'
        if normalized_format not in {'pdf', 'xlsx', 'csv'}:
            raise ValidationError(_('Unsupported report export format.'))

        rows = self._build_export_rows(report)
        if normalized_format == 'xlsx':
            content = self._build_xlsx_bytes(rows)
            response = HttpResponse(
                content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = f'attachment; filename="{report.report_no}.xlsx"'
            return response

        if normalized_format == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            for row in rows:
                writer.writerow(row)
            response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{report.report_no}.csv"'
            return response

        pdf_content = self._build_pdf_bytes(report, rows)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{report.report_no}.pdf"'
        return response

    @staticmethod
    def _validate_task_for_report(task: InventoryTask) -> None:
        """Ensure a task is ready for reporting."""
        if task.status != InventoryTask.STATUS_COMPLETED:
            raise ValidationError(_('Only completed inventory tasks can generate reports.'))

    def _build_report_payload(self, task: InventoryTask) -> Dict[str, Any]:
        """Build structured summary payload for a report."""
        differences = list(
            InventoryDifference.objects.filter(
                task_id=task.id,
                is_deleted=False,
            ).select_related('asset', 'asset__department')
        )
        total_assets = int(task.total_count or 0)
        scanned_assets = int(task.scanned_count or 0)
        difference_count = len(differences)
        department_summary: Dict[str, Dict[str, int]] = {}
        type_summary: Dict[str, int] = {}
        difference_rows: List[Dict[str, Any]] = []

        for snapshot in task.snapshots.all():
            department_key = str(snapshot.department_name or _('Unassigned'))
            department_summary.setdefault(
                department_key,
                {'department': department_key, 'total': 0, 'scanned': 0, 'differences': 0},
            )
            department_summary[department_key]['total'] += 1
            if snapshot.scanned:
                department_summary[department_key]['scanned'] += 1

        for diff in differences:
            department_name = ''
            if diff.asset and getattr(diff.asset, 'department', None):
                department_name = diff.asset.department.name or ''
            department_key = str(department_name or _('Unassigned'))
            department_summary.setdefault(
                department_key,
                {'department': department_key, 'total': 0, 'scanned': 0, 'differences': 0},
            )
            department_summary[department_key]['differences'] += 1
            type_summary[diff.difference_type] = type_summary.get(diff.difference_type, 0) + 1
            difference_rows.append(
                {
                    'type': str(diff.get_difference_type_display()),
                    'asset': getattr(diff.asset, 'asset_name', '') or diff.description,
                    'asset_no': getattr(diff.asset, 'asset_code', ''),
                    'value': str(diff.quantity_difference or 0),
                    'description': str(diff.description or ''),
                    'status': str(diff.get_status_display()),
                }
            )

        recommendations = self._build_recommendations(task, difference_count)
        summary = {
            'task_no': task.task_code,
            'task_name': task.task_name,
            'period_start': task.started_at.isoformat() if task.started_at else None,
            'period_end': task.completed_at.isoformat() if task.completed_at else None,
            'total_assets': total_assets,
            'scanned_assets': scanned_assets,
            'unscanned_assets': max(total_assets - scanned_assets, 0),
            'scan_rate': f'{round((scanned_assets / total_assets) * 100, 2)}%' if total_assets else '0%',
            'difference_count': difference_count,
            'difference_rate': f'{round((difference_count / total_assets) * 100, 2)}%' if total_assets else '0%',
        }
        report_data = {
            'summary': summary,
            'differences_by_type': type_summary,
            'differences_by_department': list(department_summary.values()),
            'differences_detail': difference_rows,
            'recommendations': recommendations,
        }
        return {
            'summary': summary,
            'report_data': report_data,
        }

    @staticmethod
    def _build_recommendations(task: InventoryTask, difference_count: int) -> List[str]:
        """Build plain-language recommendations for a generated report."""
        recommendations = []
        if difference_count == 0:
            recommendations.append(
                str(_('No inventory differences were found. Proceed with normal archive and closure.'))
            )
        else:
            recommendations.append(
                str(_('Prioritize unresolved differences and complete downstream correction actions.'))
            )
        if int(task.missing_count or 0) > 0:
            recommendations.append(
                str(_('Investigate missing assets and confirm whether disposal or transfer records are missing.'))
            )
        if int(task.damaged_count or 0) > 0:
            recommendations.append(
                str(_('Coordinate maintenance or disposal handling for damaged assets.'))
            )
        return recommendations

    def _build_export_rows(self, report: InventoryReport) -> List[List[str]]:
        """Build a flat export table for spreadsheet and PDF generation."""
        summary = dict(report.summary or {})
        report_data = dict(report.report_data or {})
        difference_rows = list(report_data.get('differences_detail') or [])

        rows: List[List[str]] = [
            ['Report No', report.report_no],
            ['Task No', str(summary.get('task_no') or '')],
            ['Task Name', str(summary.get('task_name') or '')],
            ['Status', report.get_status_display()],
            ['Generated At', report.generated_at.isoformat() if report.generated_at else ''],
            ['Generated By', _user_display_name(report.generated_by)],
            ['Total Assets', str(summary.get('total_assets') or 0)],
            ['Scanned Assets', str(summary.get('scanned_assets') or 0)],
            ['Difference Count', str(summary.get('difference_count') or 0)],
            [],
            ['Difference Type', 'Asset', 'Asset No', 'Quantity Delta', 'Status', 'Description'],
        ]
        for row in difference_rows:
            rows.append(
                [
                    str(row.get('type') or ''),
                    str(row.get('asset') or ''),
                    str(row.get('asset_no') or ''),
                    str(row.get('value') or ''),
                    str(row.get('status') or ''),
                    str(row.get('description') or ''),
                ]
            )
        return rows

    def _build_xlsx_bytes(self, rows: Iterable[Iterable[str]]) -> bytes:
        """Build a minimal XLSX workbook using only the Python standard library."""
        workbook = BytesIO()
        with ZipFile(workbook, 'w', ZIP_DEFLATED) as archive:
            archive.writestr(
                '[Content_Types].xml',
                """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>""",
            )
            archive.writestr(
                '_rels/.rels',
                """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
            )
            archive.writestr(
                'xl/workbook.xml',
                """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Inventory Report" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>""",
            )
            archive.writestr(
                'xl/_rels/workbook.xml.rels',
                """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>""",
            )
            archive.writestr(
                'xl/styles.xml',
                """<?xml version="1.0" encoding="UTF-8"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border/></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
</styleSheet>""",
            )
            archive.writestr('xl/worksheets/sheet1.xml', self._build_sheet_xml(rows))
        return workbook.getvalue()

    def _build_sheet_xml(self, rows: Iterable[Iterable[str]]) -> str:
        """Build worksheet XML for the export workbook."""
        row_xml: List[str] = []
        for row_index, row in enumerate(rows, start=1):
            cells: List[str] = []
            for column_index, value in enumerate(row, start=1):
                cell_ref = f'{self._column_name(column_index)}{row_index}'
                cell_value = escape(str(value or ''))
                cells.append(
                    f'<c r="{cell_ref}" t="inlineStr"><is><t>{cell_value}</t></is></c>'
                )
            row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetData>'
            f'{"".join(row_xml)}'
            '</sheetData>'
            '</worksheet>'
        )

    @staticmethod
    def _column_name(index: int) -> str:
        """Convert a 1-based column index into an Excel column label."""
        value = index
        result = ''
        while value > 0:
            value, remainder = divmod(value - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def _build_pdf_bytes(self, report: InventoryReport, rows: List[List[str]]) -> bytes:
        """Build a compact PDF document using the native PDF text syntax."""
        lines = [report.report_no]
        for row in rows[1:]:
            if not row:
                lines.append('')
                continue
            lines.append(' | '.join(str(item or '') for item in row))

        escaped_lines = [self._escape_pdf_text(line)[:110] for line in lines[:40]]
        text_commands = ['BT', '/F1 11 Tf', '40 790 Td']
        for index, line in enumerate(escaped_lines):
            if index == 0:
                text_commands.append(f'({line}) Tj')
            else:
                text_commands.append('0 -16 Td')
                text_commands.append(f'({line}) Tj')
        text_commands.append('ET')
        content_stream = '\n'.join(text_commands).encode('utf-8')
        return self._wrap_pdf_stream(content_stream)

    @staticmethod
    def _escape_pdf_text(value: str) -> str:
        """Escape PDF text content."""
        ascii_value = str(value).encode('ascii', 'ignore').decode('ascii')
        return ascii_value.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    @staticmethod
    def _wrap_pdf_stream(content_stream: bytes) -> bytes:
        """Wrap a text stream into a valid single-page PDF."""
        objects = [
            b'<< /Type /Catalog /Pages 2 0 R >>',
            b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
            (
                b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] '
                b'/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>'
            ),
            b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
            b'<< /Length %d >>\nstream\n%s\nendstream' % (len(content_stream), content_stream),
        ]

        pdf = bytearray(b'%PDF-1.4\n')
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f'{index} 0 obj\n'.encode('utf-8'))
            pdf.extend(obj)
            pdf.extend(b'\nendobj\n')

        xref_offset = len(pdf)
        pdf.extend(f'xref\n0 {len(objects) + 1}\n'.encode('utf-8'))
        pdf.extend(b'0000000000 65535 f \n')
        for offset in offsets[1:]:
            pdf.extend(f'{offset:010d} 00000 n \n'.encode('utf-8'))
        pdf.extend(
            (
                f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n'
                f'startxref\n{xref_offset}\n%%EOF'
            ).encode('utf-8')
        )
        return bytes(pdf)
