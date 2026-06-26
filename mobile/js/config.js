// 服务端 API 地址（手机端独立部署时修改此处）
// 演示时改为电脑/云服务器的局域网 IP，例如：http://192.168.1.100:8000/api
window.APP_CONFIG = {
  API_BASE: 'http://localhost:8000/api',
  MOCK_MODE: false, // 启用 Mock 模式（无需后端）
};
window.API_BASE = window.APP_CONFIG.API_BASE;
window.MOCK_MODE = window.APP_CONFIG.MOCK_MODE;
