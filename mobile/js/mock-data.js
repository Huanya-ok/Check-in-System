/**
 * Mock 模式 - API 拦截器
 * 
 * 当 MOCK_MODE = true 时,拦截所有 fetch 请求并返回模拟数据
 * 数据存储在 localStorage 中,刷新页面后数据仍然保留
 */

// ==================== 模拟初始数据 ====================

const MOCK_INITIAL_DATA = {
  // 预置用户(包括教师账号)
  users: [
    {
      id: 1,
      username: 'teacher',
      password_hash: 'teacher123', // Mock 模式下明文存储
      name: '王老师',
      student_no: 'T001',
      role: 'teacher',
      created_at: new Date().toISOString()
    },
    {
      id: 2,
      username: 'zhangsan',
      password_hash: '123456',
      name: '张三',
      student_no: '231250197',
      role: 'student',
      created_at: new Date().toISOString()
    },
    {
      id: 3,
      username: 'lisi',
      password_hash: '123456',
      name: '李四',
      student_no: '231250050',
      role: 'student',
      created_at: new Date().toISOString()
    }
  ],
  
  // 人脸底库(与用户一对一)
  face_profiles: [
    {
      id: 1,
      user_id: 2,
      name: '张三',
      student_no: '231250197',
      photo_path: '/uploads/face_zhangsan.jpg',
      frs_face_id: 'frs_001',
      is_active: true,
      created_at: new Date().toISOString()
    },
    {
      id: 2,
      user_id: 3,
      name: '李四',
      student_no: '231250050',
      photo_path: '/uploads/face_lisi.jpg',
      frs_face_id: 'frs_002',
      is_active: true,
      created_at: new Date().toISOString()
    }
  ],
  
  // 签到记录
  check_in_records: [
    {
      id: 1,
      face_profile_id: 1,
      check_in_time: new Date(Date.now() - 86400000).toISOString(), // 昨天
      similarity_score: 0.92,
      photo_path: '/uploads/checkin_001.jpg'
    },
    {
      id: 2,
      face_profile_id: 1,
      check_in_time: new Date().toISOString(), // 今天
      similarity_score: 0.88,
      photo_path: '/uploads/checkin_002.jpg'
    }
  ]
};

// ==================== 工具函数 ====================

function initMockData() {
  if (!localStorage.getItem('mock_initialized')) {
    localStorage.setItem('mock_users', JSON.stringify(MOCK_INITIAL_DATA.users));
    localStorage.setItem('mock_face_profiles', JSON.stringify(MOCK_INITIAL_DATA.face_profiles));
    localStorage.setItem('mock_check_in_records', JSON.stringify(MOCK_INITIAL_DATA.check_in_records));
    localStorage.setItem('mock_initialized', 'true');
    console.log('[Mock] 初始数据已加载');
  }
}

function getMockData(key) {
  const data = localStorage.getItem(`mock_${key}`);
  return data ? JSON.parse(data) : [];
}

function setMockData(key, data) {
  localStorage.setItem(`mock_${key}`, JSON.stringify(data));
}

function generateId() {
  return Date.now() + Math.floor(Math.random() * 1000);
}

function generateToken(user) {
  // Mock JWT token (实际项目中应使用真实 JWT)
  return `mock_token_${user.id}_${Date.now()}`;
}

// ==================== API 路由处理 ====================

async function handleMockRequest(url, options) {
  const method = options.method || 'GET';
  
  // 解析URL，分离路径和查询参数
  const urlObj = new URL(url);
  let path = urlObj.pathname;  // 例如: "/api/check-in/records"
  
  // 移除 API 前缀（如果存在）
  // API_BASE 可能是 "http://localhost:8000/api" 或 "http://localhost:8000"
  const apiBasePath = new URL(API_BASE).pathname;  // "/api" 或 "/"
  if (apiBasePath !== '/' && path.startsWith(apiBasePath)) {
    path = path.substring(apiBasePath.length);  // "/api/check-in/records" -> "/check-in/records"
  }
  
  console.log(`[Mock] ${method} ${path}`);
  
  // 健康检查
  if (path === '/health') {
    return mockResponse({ status: 'ok', timestamp: new Date().toISOString() });
  }
  
  // ==================== 认证相关 ====================
  
  // 注册
  if (path === '/auth/register' && method === 'POST') {
    return await handleRegister(options.body);
  }
  
  // 登录
  if (path === '/auth/login' && method === 'POST') {
    return await handleLogin(options.body);
  }
  
  // 注销
  if (path === '/auth/logout' && method === 'POST') {
    return mockResponse({ message: '注销成功' });
  }
  
  // ==================== 签到相关 ====================
  
  // 签到
  if (path === '/check-in' && method === 'POST') {
    return await handleCheckIn(options.body);
  }
  
  // 查询个人签到记录
  if (path === '/check-in/records' && method === 'GET') {
    return await handleGetRecords(url);  // 传递完整URL以获取查询参数
  }
  
  // ==================== 教师总览 ====================
  
  // 教师签到总览
  if (path === '/teacher/overview' && method === 'GET') {
    return await handleTeacherOverview(url);
  }
  
  // 未匹配的路由
  console.log('[Mock] Route not found:', path);
  return mockResponse({ error: 'Not Found' }, 404);
}

// ==================== 业务逻辑处理 ====================

async function handleRegister(formData) {
  // 解析 FormData
  const data = {};
  for (const [key, value] of formData.entries()) {
    if (value instanceof File) {
      data[key] = { name: value.name, size: value.size };
    } else {
      data[key] = value;
    }
  }
  
  const users = getMockData('users');
  const faceProfiles = getMockData('face_profiles');
  
  // 检查用户名是否已存在
  if (users.find(u => u.username === data.username)) {
    return mockResponse({ detail: '用户名已存在' }, 400);
  }
  
  // 检查学号是否已存在
  if (users.find(u => u.student_no === data.student_no)) {
    return mockResponse({ detail: '学号已被注册' }, 400);
  }
  
  // 创建新用户
  const newUser = {
    id: generateId(),
    username: data.username,
    password_hash: data.password,
    name: data.name,
    student_no: data.student_no,
    role: 'student',
    created_at: new Date().toISOString()
  };
  
  users.push(newUser);
  setMockData('users', users);
  
  // 创建人脸底库
  const newProfile = {
    id: generateId(),
    user_id: newUser.id,
    name: data.name,
    student_no: data.student_no,
    photo_path: `/uploads/face_${newUser.id}.jpg`,
    frs_face_id: `frs_${generateId()}`,
    is_active: true,
    created_at: new Date().toISOString()
  };
  
  faceProfiles.push(newProfile);
  setMockData('face_profiles', faceProfiles);
  
  // 生成 Token
  const token = generateToken(newUser);
  
  return mockResponse({
    message: '注册成功',
    access_token: token,
    username: newUser.username,
    name: newUser.name,
    role: newUser.role
  });
}

async function handleLogin(bodyStr) {
  const body = JSON.parse(bodyStr);
  const users = getMockData('users');
  
  const user = users.find(u => u.username === body.username && u.password_hash === body.password);
  
  if (!user) {
    return mockResponse({ detail: '用户名或密码错误' }, 401);
  }
  
  const token = generateToken(user);
  
  // 模拟网络延迟
  await sleep(300);
  
  return mockResponse({
    access_token: token,
    username: user.username,
    name: user.name,
    role: user.role
  });
}

async function handleCheckIn(formData) {
  // 在 Mock 模式下,随机匹配一个学生
  const faceProfiles = getMockData('face_profiles');
  const records = getMockData('check_in_records');
  
  if (faceProfiles.length === 0) {
    return mockResponse({ 
      success: false, 
      message: '系统中暂无注册用户,请先注册' 
    }, 404);
  }
  
  // 随机选择一个已注册的学生进行"识别"
  const randomProfile = faceProfiles[Math.floor(Math.random() * faceProfiles.length)];
  
  // 创建签到记录
  const newRecord = {
    id: generateId(),
    face_profile_id: randomProfile.id,
    check_in_time: new Date().toISOString(),
    similarity_score: 0.85 + Math.random() * 0.1, // 85%~95% 相似度
    photo_path: `/uploads/checkin_${generateId()}.jpg`
  };
  
  records.push(newRecord);
  setMockData('check_in_records', records);
  
  // 模拟人脸识别延迟
  await sleep(800);
  
  return mockResponse({
    success: true,
    name: randomProfile.name,
    student_no: randomProfile.student_no,
    message: `签到成功！欢迎 ${randomProfile.name}`
  });
}

async function handleGetRecords(url) {
  // 从 URL 提取日期参数
  const urlObj = new URL(url);
  const dateParam = urlObj.searchParams.get('date');
  
  const records = getMockData('check_in_records');
  const faceProfiles = getMockData('face_profiles');
  
  // 获取当前登录用户的 face_profile_id
  const token = localStorage.getItem('token');
  if (!token) {
    return mockResponse({ detail: '未授权' }, 401);
  }
  
  // 从 token 中提取用户 ID (Mock token 格式: mock_token_{userId}_{timestamp})
  const userId = parseInt(token.split('_')[2]);
  const userProfile = faceProfiles.find(p => p.user_id === userId);
  
  if (!userProfile) {
    return mockResponse([]);
  }
  
  // 筛选该用户的签到记录
  let userRecords = records.filter(r => r.face_profile_id === userProfile.id);
  
  // 如果指定了日期,进一步筛选
  if (dateParam) {
    userRecords = userRecords.filter(r => {
      // 将记录的UTC时间转换为本地时区的日期字符串 (YYYY-MM-DD)
      const recordDate = new Date(r.check_in_time);
      const recordYear = recordDate.getFullYear();
      const recordMonth = String(recordDate.getMonth() + 1).padStart(2, '0');
      const recordDay = String(recordDate.getDate()).padStart(2, '0');
      const recordDateStr = `${recordYear}-${recordMonth}-${recordDay}`;

      return recordDateStr === dateParam;
    });
  }
  
  // 按时间倒序排列
  userRecords.sort((a, b) => new Date(b.check_in_time) - new Date(a.check_in_time));
  
  // 格式化响应数据，与后端 CheckInRecordResponse 保持一致
  const formattedRecords = userRecords.map(record => ({
    id: record.id,
    face_profile_id: record.face_profile_id,
    name: userProfile.name,
    student_no: userProfile.student_no,
    check_in_time: record.check_in_time,
    similarity_score: record.similarity_score
    // 注意：不包含 photo_path，与后端保持一致
  }));
  
  console.log('[Mock] Returning', formattedRecords.length, 'formatted records');
  
  await sleep(200);
  
  return mockResponse(formattedRecords);
}

async function handleTeacherOverview(url) {
  const urlObj = new URL(url);
  const dateParam = urlObj.searchParams.get('date') || new Date().toISOString().slice(0, 10);
  
  const users = getMockData('users');
  const faceProfiles = getMockData('face_profiles');
  const records = getMockData('check_in_records');
  
  // 获取所有学生用户
  const studentUsers = users.filter(u => u.role === 'student');
  const totalRegistered = studentUsers.length;
  
  // 获取指定日期的签到记录
  const dayRecords = records.filter(r => {
    const recordDate = new Date(r.check_in_time).toISOString().slice(0, 10);
    return recordDate === dateParam;
  });
  
  // 已签到的学生
  const checkedInProfileIds = [...new Set(dayRecords.map(r => r.face_profile_id))];
  const checkedInCount = checkedInProfileIds.length;
  
  // 构建已签到明细
  const checkedInRecords = dayRecords.map(record => {
    const profile = faceProfiles.find(p => p.id === record.face_profile_id);
    return {
      id: record.id,
      name: profile ? profile.name : '未知',
      student_no: profile ? profile.student_no : 'N/A',
      check_in_time: record.check_in_time,
      similarity_score: record.similarity_score
    };
  });
  
  // 未签到的学生
  const absentStudents = studentUsers
    .filter(user => {
      const profile = faceProfiles.find(p => p.user_id === user.id);
      return !profile || !checkedInProfileIds.includes(profile.id);
    })
    .map(user => ({
      name: user.name,
      student_no: user.student_no
    }));
  
  await sleep(300);
  
  return mockResponse({
    date: dateParam,
    total_registered: totalRegistered,
    checked_in_count: checkedInCount,
    absent_count: absentStudents.length,
    records: checkedInRecords,
    absent_students: absentStudents
  });
}

// ==================== 辅助函数 ====================

function mockResponse(data, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status: status,
    json: async () => data
  };
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ==================== 拦截 Fetch ====================

if (window.MOCK_MODE) {
  console.log('[Mock] Mock 模式已启用');
  initMockData();
  
  // 保存原始 fetch
  const originalFetch = window.fetch;
  
  // 重写 fetch
  window.fetch = async function(url, options = {}) {
    // 判断是否是 API 请求
    if (typeof url === 'string' && url.startsWith(API_BASE)) {
      console.log('[Mock] 拦截 API 请求:', url);
      return await handleMockRequest(url, options);
    }
    
    // 非 API 请求使用原始 fetch
    return originalFetch.apply(this, arguments);
  };
  
  console.log('[Mock] Fetch 拦截器已安装');
}
