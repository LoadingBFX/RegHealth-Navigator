export const config = {
    api: {
      baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8080',
      endpoints: {
        summarize: {
          list: '/api/summarize/list',
          generate: '/api/summarize'
        },
        chat: '/api/chat'
      }
    }
  };
  
  console.log('Environment:', import.meta.env.MODE);
  console.log('API Base URL:', config.api.baseUrl);
  console.log('Full Config:', config);
  
  export default config;
