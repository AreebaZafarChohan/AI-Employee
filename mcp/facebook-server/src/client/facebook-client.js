/**
 * Facebook Client - Graph API Integration
 * 
 * Connects to Facebook Graph API v18.0
 */

import fetch from 'node-fetch';

export class FacebookClient {
  constructor(config) {
    this.accessToken = config.access_token;
    this.pageId = config.page_id || 'me';
    this.apiVersion = config.api_version || 'v18.0';
    this.base_url = `https://graph.facebook.com/${this.apiVersion}`;
    this.timeout = config.timeout || 30000;
  }

  /**
   * Make authenticated request to Graph API
   */
  async request(endpoint, method = 'GET', params = {}) {
    try {
      const url = new URL(`${this.base_url}/${endpoint}`);
      url.searchParams.append('access_token', this.accessToken);

      const options = {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
      };

      if (method === 'POST' && Object.keys(params).length > 0) {
        options.body = JSON.stringify(params);
      } else if (method === 'GET' && Object.keys(params).length > 0) {
        Object.entries(params).forEach(([key, value]) => {
          url.searchParams.append(key, value);
        });
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url.toString(), {
        ...options,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const result = await response.json();

      if (result.error) {
        throw new Error(`Facebook API error: ${result.error.message}`);
      }

      return result;
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error(`Facebook request timeout after ${this.timeout}ms`);
      }
      throw new Error(`Facebook API error: ${error.message}`);
    }
  }

  /**
   * Get Page Information
   */
  async getPageInfo(pageId = null) {
    const id = pageId || this.pageId;
    return this.request(id, 'GET', {
      fields: 'id,name,about,category,followers_count,likes,website,username'
    });
  }

  /**
   * Publish a post to Facebook Page
   */
  async publishPost(message, options = {}) {
    const params = {
      message,
    };

    if (options.link) {
      params.link = options.link;
    }

    if (options.photo) {
      params.picture = options.photo;
    }

    if (options.scheduled_at) {
      params.published = false;
      params.scheduled_publish_time = Math.floor(new Date(options.scheduled_at).getTime() / 1000);
    }

    return this.request(`${this.pageId}/feed`, 'POST', params);
  }

  /**
   * Schedule a post for later
   */
  async schedulePost(message, scheduledAt, options = {}) {
    return this.publishPost(message, {
      ...options,
      scheduled_at: scheduledAt,
    });
  }

  /**
   * Get Page Insights
   */
  async getInsights(metrics = null, since = null, until = null) {
    const params = {
      fields: metrics || 'page_impressions,page_engagements,page_post_engagements,page_likes',
    };

    if (since) {
      params.since = since;
    }

    if (until) {
      params.until = until;
    }

    return this.request(`${this.pageId}/insights`, 'GET', params);
  }

  /**
   * Get Page Posts
   */
  async getPosts(limit = 10) {
    return this.request(`${this.pageId}/posts`, 'GET', { limit });
  }

  /**
   * Reply to a comment
   */
  async replyToComment(commentId, message) {
    return this.request(`${commentId}/comments`, 'POST', {
      message,
      can_comment: true,
    });
  }

  /**
   * Get Comments on a post
   */
  async getComments(postId, limit = 10) {
    return this.request(`${postId}/comments`, 'GET', {
      limit,
      fields: 'from,message,created_time,like_count',
    });
  }

  /**
   * Upload a photo
   */
  async uploadPhoto(photoUrl, message = '') {
    return this.request(`${this.pageId}/photos`, 'POST', {
      url: photoUrl,
      message,
    });
  }
}
