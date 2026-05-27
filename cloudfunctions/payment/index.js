// 支付云函数
const cloud = require('tt-server-sdk');
cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV
});

const db = cloud.database();
const _ = db.command;

exports.main = async (event, context) => {
  const { action, version, orderId } = event;
  const wxContext = cloud.getWXContext();
  const openid = wxContext.OPENID;
  
  console.log('支付请求', { action, version, orderId, openid });
  
  switch (action) {
    case 'create':
      return await createOrder(version, openid);
    case 'check':
      return await checkPayment(orderId, openid);
    case 'simulate':
      return await simulatePayment(orderId, openid);
    default:
      return {
        success: false,
        message: '未知操作'
      };
  }
};

// 创建订单
async function createOrder(version, openid) {
  const prices = {
    deep: 9.9,
    vip: 19.9
  };
  
  const names = {
    deep: '深度版',
    vip: 'VIP版'
  };
  
  const orderId = generateOrderId(version);
  
  try {
    await db.collection('orders').add({
      orderId: orderId,
      openid: openid,
      version: version,
      amount: prices[version] || 0,
      productName: names[version] || '服务',
      status: 'pending', // pending, paid, cancelled
      createdAt: new Date(),
      paidAt: null
    });
    
    return {
      success: true,
      orderId: orderId,
      version: version,
      amount: prices[version] || 0,
      name: names[version] || '服务'
    };
  } catch (error) {
    console.error('创建订单失败', error);
    return {
      success: false,
      message: '创建订单失败'
    };
  }
}

// 检查支付状态
async function checkPayment(orderId, openid) {
  try {
    const result = await db.collection('orders')
      .where({
        orderId: orderId,
        openid: openid
      })
      .get();
    
    if (result.data.length === 0) {
      return {
        paid: false,
        message: '订单不存在'
      };
    }
    
    const order = result.data[0];
    
    return {
      paid: order.status === 'paid',
      version: order.version,
      paidAt: order.paidAt
    };
  } catch (error) {
    console.error('检查订单失败', error);
    return {
      paid: false,
      message: '查询失败'
    };
  }
}

// 模拟支付（测试用）
async function simulatePayment(orderId, openid) {
  try {
    const result = await db.collection('orders')
      .where({
        orderId: orderId,
        openid: openid
      })
      .get();
    
    if (result.data.length === 0) {
      return {
        success: false,
        message: '订单不存在'
      };
    }
    
    const order = result.data[0];
    
    // 更新订单状态
    await db.collection('orders')
      .doc(order._id)
      .update({
        status: 'paid',
        paidAt: new Date()
      });
    
    // 记录用户权限
    await db.collection('user_privileges')
      .add({
        openid: openid,
        version: order.version,
        orderId: orderId,
        validUntil: getValidUntil(),
        createdAt: new Date()
      });
    
    return {
      success: true,
      paid: true
    };
  } catch (error) {
    console.error('模拟支付失败', error);
    return {
      success: false,
      message: '操作失败'
    };
  }
}

// 生成订单号
function generateOrderId(version) {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8).toUpperCase();
  return `${version.toUpperCase()}_${timestamp}_${random}`;
}

// 获取有效期（1年）
function getValidUntil() {
  const date = new Date();
  date.setFullYear(date.getFullYear() + 1);
  return date;
}
