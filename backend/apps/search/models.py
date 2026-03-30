"""Models for smart search history, saved searches, and suggestions."""
from django.db import models
from django.db.models import Q

from apps.common.models import BaseModel


class SearchType(models.TextChoices):
    """Supported search domains."""

    ASSET = 'asset', 'Asset'
    PROJECT = 'project', 'Project'
    LOAN = 'loan', 'Loan'


class SearchHistory(BaseModel):
    """Stores user search history for quick repeat access."""

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='search_histories',
        help_text='User who executed the search',
    )
    search_type = models.CharField(
        max_length=20,
        choices=SearchType.choices,
        default=SearchType.ASSET,
        help_text='Search domain type',
    )
    keyword = models.CharField(
        max_length=200,
        blank=True,
        help_text='Original keyword entered by the user',
    )
    normalized_keyword = models.CharField(
        max_length=200,
        blank=True,
        db_index=True,
        help_text='Normalized keyword for deduplication',
    )
    query_signature = models.CharField(
        max_length=64,
        db_index=True,
        help_text='Stable signature for keyword and filters',
    )
    filters = models.JSONField(
        default=dict,
        blank=True,
        help_text='Applied filter payload',
    )
    result_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of results returned by the last execution',
    )
    search_count = models.PositiveIntegerField(
        default=1,
        help_text='How many times the same search was repeated',
    )
    last_searched_at = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp of the latest execution',
    )

    class Meta:
        db_table = 'search_history'
        verbose_name = 'Search History'
        verbose_name_plural = 'Search Histories'
        ordering = ['-last_searched_at', '-updated_at', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'user', 'search_type']),
            models.Index(fields=['organization', 'search_type', 'last_searched_at']),
            models.Index(fields=['organization', 'normalized_keyword']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'user', 'search_type', 'query_signature'],
                condition=Q(is_deleted=False),
                name='uniq_search_history_signature_org_user',
            ),
        ]

    def __str__(self):
        return f'{self.user_id}:{self.search_type}:{self.keyword}'


class SavedSearch(BaseModel):
    """Stores reusable search presets for a user or an organization."""

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='saved_searches',
        help_text='Owner of the saved search',
    )
    name = models.CharField(
        max_length=100,
        help_text='Display name for the saved search',
    )
    search_type = models.CharField(
        max_length=20,
        choices=SearchType.choices,
        default=SearchType.ASSET,
        help_text='Search domain type',
    )
    keyword = models.CharField(
        max_length=200,
        blank=True,
        help_text='Default keyword for the saved search',
    )
    filters = models.JSONField(
        default=dict,
        blank=True,
        help_text='Saved filter payload',
    )
    is_shared = models.BooleanField(
        default=False,
        help_text='Whether the search is visible to other users in the organization',
    )
    use_count = models.PositiveIntegerField(
        default=0,
        help_text='How many times the saved search was used',
    )

    class Meta:
        db_table = 'saved_search'
        verbose_name = 'Saved Search'
        verbose_name_plural = 'Saved Searches'
        ordering = ['-updated_at', '-created_at', 'name']
        indexes = [
            models.Index(fields=['organization', 'user', 'search_type']),
            models.Index(fields=['organization', 'search_type', 'is_shared']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'user', 'name'],
                condition=Q(is_deleted=False),
                name='uniq_saved_search_name_org_user',
            ),
        ]

    def __str__(self):
        return self.name


class SearchSuggestion(BaseModel):
    """Caches suggestion candidates generated from past searches."""

    search_type = models.CharField(
        max_length=20,
        choices=SearchType.choices,
        default=SearchType.ASSET,
        help_text='Search domain type',
    )
    query = models.CharField(
        max_length=200,
        help_text='Suggestion text displayed to users',
    )
    normalized_query = models.CharField(
        max_length=200,
        db_index=True,
        help_text='Normalized suggestion text used for matching',
    )
    frequency = models.PositiveIntegerField(
        default=1,
        help_text='Usage frequency for ranking suggestions',
    )
    last_used = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp of the latest usage',
    )

    class Meta:
        db_table = 'search_suggestion'
        verbose_name = 'Search Suggestion'
        verbose_name_plural = 'Search Suggestions'
        ordering = ['-frequency', '-last_used', 'query']
        indexes = [
            models.Index(fields=['organization', 'search_type', 'normalized_query']),
            models.Index(fields=['organization', 'search_type', 'last_used']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'search_type', 'normalized_query'],
                condition=Q(is_deleted=False),
                name='uniq_search_suggestion_org_type_query',
            ),
        ]

    def __str__(self):
        return self.query
