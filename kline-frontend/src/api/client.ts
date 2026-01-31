import axios from 'axios';
import { message } from 'antd';
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
    // 如果是取消的请求，不显示错误
    if (axios.isCancel(error)) {
      logger.info('请求已取消', error.message);
      return Promise.reject(error);
    }

    // 错误处理
    if (error.response) {
      // 服务器返回错误响应
      const errorMsg = error.response.data?.detail ||
                       error.response.data?.message ||
                       `服务器错误 (${error.response.status})`;

      logger.error('API错误响应', {
        url: error.config?.url,
        status: error.response.status,
        data: error.response.data,
      });

      message.error(errorMsg);
    } else if (error.request) {
      // 网络错误（无响应）
      logger.error('网络错误', {
        url: error.config?.url,
        message: error.message,
      });

      message.error('网络连接失败，请检查后端服务是否启动');
    } else {
      // 请求配置错误
      logger.error('请求配置错误', error.message);
      message.error('请求配置错误');
    }

    return Promise.reject(error);
  }
);

export default apiClient;
