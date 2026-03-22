/**
 * Instagram Client - Graph API Integration
 * 
 * Connects to Instagram Graph API v18.0
 */

import fetch from 'node-fetch';

export class InstagramClient {
  constructor(config) {
    this.accessToken = config.access_token;
    this.instagramBusinessAccountId = config.business_account_id;
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
        throw new Error(`Instagram API error: ${result.error.message}`);
      }

      return result;
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error(`Instagram request timeout after ${this.timeout}ms`);
      }
      throw new Error(`Instagram API error: ${error.message}`);
    }
  }

  /**
   * Get Instagram Business Account Info
   */
  async getAccountInfo() {
    return this.request(this.instagramBusinessAccountId, 'GET', {
      fields: 'id,name,username,biography,website,followers_count,follows_count,media_count'
    });
  }

  /**
   * Get Recent Media
   */
  async getMedia(limit = 10) {
    return this.request(`${this.instagramBusinessAccountId}/media`, 'GET', {
      limit,
      fields: 'id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count'
    });
  }

  /**
   * Create Media Container (for posts)
   */
  async createMediaContainer(caption, mediaUrl, mediaType = 'IMAGE') {
    const params = {
      image_source: mediaUrl,
      caption: caption,
      access_token: this.accessToken,
    };

    if (mediaType === 'VIDEO') {
      params.video_url = mediaUrl;
      delete params.image_source;
    } else if (mediaType === 'CAROUSEL') {
      params.media_type = 'CAROUSEL';
    }

    return this.request(`${this.instagramBusinessAccountId}/media`, 'POST', params);
  }

  /**
   * Publish Media Container
   */
  async publishMediaContainer(creationId) {
    return this.request(`${this.instagramBusinessAccountId}/media_publish`, 'POST', {
      creation_id: creationId,
      access_token: this.accessToken,
    });
  }

  /**
   * Publish a Post (create + publish)
   */
  async publishPost(caption, mediaUrl, mediaType = 'IMAGE') {
    // Step 1: Create container
    const container = await this.createMediaContainer(caption, mediaUrl, mediaType);
    
    // Step 2: Publish container
    const publishResult = await this.publishMediaContainer(container.id);
    
    return {
      id: publishResult.id,
      status: 'published',
    };
  }

  /**
   * Get Media Insights
   */
  async getMediaInsights(mediaId, metrics = null) {
    const fields = metrics || 'impressions,reach,engagement,saved,video_views';
    return this.request(`${mediaId}/insights`, 'GET', {
      metric: fields,
    });
  }

  /**
   * Get Account Insights
   */
  async getAccountInsights(metrics = null, period = 'day') {
    const fields = metrics || 'follower_count,reach,impressions,profile_views';
    return this.request(`${this.instagramBusinessAccountId}/insights`, 'GET', {
      metric: fields,
      period,
    });
  }

  /**
   * Get Story Insights
   */
  async getStoryInsights(storyId) {
    return this.request(`${storyId}/insights`, 'GET', {
      metric: 'reach,impressions,replies,exits',
    });
  }

  /**
   * Reply to Comment
   */
  async replyToComment(mediaId, commentId, message) {
    return this.request(`${commentId}/comments`, 'POST', {
      message,
      access_token: this.accessToken,
    });
  }

  /**
   * Get Comments on Media
   */
  async getComments(mediaId, limit = 10) {
    return this.request(`${mediaId}/comments`, 'GET', {
      limit,
      fields: 'from,message,timestamp,like_count',
    });
  }
}
