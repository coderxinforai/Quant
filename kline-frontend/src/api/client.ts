import axios from 'axios';
import { logger } from '../store/useLogStore';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    logger.info(`API请求: ${config.method?.toUpperCase()} ${config.url}`, {
      params: config.params,
      data: config.data,
    });
    return config;
  },
  (error) => {
    logger.error('API请求失败', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    logger.success(`API响应: ${response.config.url}`, {
      status: response.status,
      data: response.data,
    });
    return response;
  },
  (error) => {
    if (error.response) {
      logger.error('API错误响应', {
        url: error.config?.url,
        status: error.response.status,
        data: error.response.data,
      });
    } else if (error.request) {
      logger.error('网络错误', {
        url: error.config?.url,
        message: error.message,
      });
    } else {
      logger.error('请求配置错误', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
