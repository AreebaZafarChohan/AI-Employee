/**
 * Twitter Client - Twitter API v2 Integration
 * 
 * Connects to Twitter API v2
 */

import fetch from 'node-fetch';

export class TwitterClient {
  constructor(config) {
    this.bearerToken = config.bearer_token;
    this.apiKey = config.api_key;
    this.apiSecret = config.api_secret;
    this.accessToken = config.access_token;
    this.accessSecret = config.access_token_secret;
    this.base_url = 'https://api.twitter.com/2';
    this.timeout = config.timeout || 30000;
  }

  /**
   * Make authenticated request to Twitter API v2
   */
  async request(endpoint, method = 'GET', params = {}, useOAuth = false) {
    try {
      const url = new URL(`${this.base_url}/${endpoint}`);
      
      const options = {
        method,
        headers: {
          'Authorization': `Bearer ${this.bearerToken}`,
          'Content-Type': 'application/json',
        },
      };

      // For POST requests with body
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

      if (result.errors) {
        const error = result.errors[0];
        throw new Error(`Twitter API error: ${error.message}`);
      }

      return result;
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error(`Twitter request timeout after ${this.timeout}ms`);
      }
      throw new Error(`Twitter API error: ${error.message}`);
    }
  }

  /**
   * Publish a Tweet
   */
  async publishTweet(text, options = {}) {
    const params = {
      text,
    };

    if (options.media_ids && options.media_ids.length > 0) {
      params.media = {
        media_ids: options.media_ids,
      };
    }

    if (options.reply_settings) {
      params.reply = options.reply_settings;
    }

    return this.request('tweets', 'POST', params);
  }

  /**
   * Publish a Thread (multiple tweets)
   */
  async publishThread(tweets) {
    const results = [];
    let previousTweetId = null;

    for (const tweet of tweets) {
      const tweetData = { text: tweet.content };
      
      // Add reply to previous tweet if not first
      if (previousTweetId) {
        tweetData.reply = {
          in_reply_to_tweet_id: previousTweetId,
        };
      }

      // Add media if provided
      if (tweet.media_ids && tweet.media_ids.length > 0) {
        tweetData.media = {
          media_ids: tweet.media_ids,
        };
      }

      const result = await this.publishTweet(tweetData.text, {
        media_ids: tweet.media_ids,
        reply_settings: tweetData.reply,
      });

      results.push(result);
      previousTweetId = result.data.id;
    }

    return results;
  }

  /**
   * Reply to a Tweet
   */
  async replyToTweet(tweetId, text) {
    return this.request('tweets', 'POST', {
      text,
      reply: {
        in_reply_to_tweet_id: tweetId,
      },
    });
  }

  /**
   * Retweet
   */
  async retweet(tweetId, userId = null) {
    // userId would be needed for actual implementation
    return this.request(`users/${userId || 'me'}/retweets`, 'POST', {
      tweet_id: tweetId,
    });
  }

  /**
   * Like a Tweet
   */
  async likeTweet(tweetId, userId = null) {
    return this.request(`users/${userId || 'me'}/likes`, 'POST', {
      tweet_id: tweetId,
    });
  }

  /**
   * Get Tweet by ID
   */
  async getTweet(tweetId, expansions = null) {
    const params = {
      'tweet.fields': 'created_at,author_id,public_metrics,context_annotations',
    };

    if (expansions) {
      params.expanss = expansions;
    }

    return this.request(`tweets/${tweetId}`, 'GET', params);
  }

  /**
   * Search Tweets
   */
  async searchTweets(query, options = {}) {
    const params = {
      query,
      max_results: options.max_results || 10,
      'tweet.fields': 'created_at,author_id,public_metrics',
    };

    if (options.start_time) {
      params.start_time = options.start_time;
    }

    if (options.end_time) {
      params.end_time = options.end_time;
    }

    return this.request('tweets/search/recent', 'GET', params);
  }

  /**
   * Get User by Username
   */
  async getUserByUsername(username) {
    return this.request(`users/by/username/${username}`, 'GET', {
      'user.fields': 'id,name,username,description,public_metrics,verified',
    });
  }

  /**
   * Get User's Tweets
   */
  async getUserTweets(userId, maxResults = 10) {
    return this.request(`users/${userId}/tweets`, 'GET', {
      max_results: maxResults,
      'tweet.fields': 'created_at,author_id,public_metrics,text',
    });
  }

  /**
   * Get Tweet Metrics/Analytics
   */
  async getTweetMetrics(tweetId) {
    return this.request(`tweets/${tweetId}`, 'GET', {
      'tweet.fields': 'public_metrics,non_public_metrics,organic_metrics,promoted_metrics',
    });
  }

  /**
   * Get Home Timeline
   */
  async getHomeTimeline(maxResults = 10) {
    return this.request('users/me/timelines/reverse_chronological', 'GET', {
      max_results: maxResults,
      'tweet.fields': 'created_at,author_id,public_metrics,text',
    });
  }

  /**
   * Get Mentions
   */
  async getMentions(maxResults = 10) {
    return this.request('users/me/mentions', 'GET', {
      max_results: maxResults,
      'tweet.fields': 'created_at,author_id,public_metrics,text',
    });
  }
}
