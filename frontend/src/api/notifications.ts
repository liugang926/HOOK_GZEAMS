import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

/**
 * Notifications API Client
 * Handles user notifications, templates, configs, channels, and logs
 */

// User Notifications
export const notificationApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/notifications/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/notifications/${id}/`)
  },

  markAsRead(id: string): Promise<void> {
    return request.post(`/notifications/${id}/read/`)
  },

  markAllAsRead(): Promise<void> {
    return request.post('/notifications/mark-all-read/')
  },

  delete(id: string): Promise<void> {
    return request.delete(`/notifications/${id}/`)
  },

  getUnreadCount(): Promise<{ count: number }> {
    return request.get('/notifications/unread-count/')
  }
}

// Notification Templates
export const notificationTemplateApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/notifications/templates/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/notifications/templates/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/notifications/templates/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/notifications/templates/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/notifications/templates/${id}/`)
  },

  preview(id: string, data: any): Promise<any> {
    return request.post(`/notifications/templates/${id}/preview/`, data)
  }
}

// Notification Configs
export const notificationConfigApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/notifications/configs/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/notifications/configs/${id}/`)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/notifications/configs/${id}/`, data)
  }
}

// Notification Channels
export const notificationChannelApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/notifications/channels/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/notifications/channels/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/notifications/channels/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/notifications/channels/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/notifications/channels/${id}/`)
  },

  test(id: string): Promise<void> {
    return request.post(`/notifications/channels/${id}/test/`)
  }
}

// Notification Logs
export const notificationLogApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/notifications/logs/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/notifications/logs/${id}/`)
  }
}

// In-App Messages
export const inAppMessageApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/notifications/inapp/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/notifications/inapp/${id}/`)
  },

  markAsRead(id: string): Promise<void> {
    return request.post(`/notifications/inapp/${id}/read/`)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/notifications/inapp/${id}/`)
  }
}

// Legacy function exports for backward compatibility
export const getNotificationList = notificationApi.list
export const getNotificationDetail = notificationApi.detail
export const markNotificationAsRead = notificationApi.markAsRead
export const markAllNotificationsAsRead = notificationApi.markAllAsRead
export const deleteNotification = notificationApi.delete
export const getUnreadCount = notificationApi.getUnreadCount

export const getNotificationTemplateList = notificationTemplateApi.list
export const getNotificationTemplateDetail = notificationTemplateApi.detail
export const createNotificationTemplate = notificationTemplateApi.create
export const updateNotificationTemplate = notificationTemplateApi.update
export const deleteNotificationTemplate = notificationTemplateApi.delete
export const previewNotificationTemplate = notificationTemplateApi.preview

export const getNotificationConfigList = notificationConfigApi.list
export const getNotificationConfigDetail = notificationConfigApi.detail
export const updateNotificationConfig = notificationConfigApi.update

export const getNotificationChannelList = notificationChannelApi.list
export const getNotificationChannelDetail = notificationChannelApi.detail
export const createNotificationChannel = notificationChannelApi.create
export const updateNotificationChannel = notificationChannelApi.update
export const deleteNotificationChannel = notificationChannelApi.delete
export const testNotificationChannel = notificationChannelApi.test

export const getNotificationLogList = notificationLogApi.list
export const getNotificationLogDetail = notificationLogApi.detail

export const getInAppMessageList = inAppMessageApi.list
export const getInAppMessageDetail = inAppMessageApi.detail
export const markInAppMessageAsRead = inAppMessageApi.markAsRead
export const deleteInAppMessage = inAppMessageApi.delete
