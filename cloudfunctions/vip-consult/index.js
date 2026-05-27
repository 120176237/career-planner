// VIP咨询云函数
const cloud = require('tt-server-sdk');
cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV
});

const db = cloud.database();

exports.main = async (event, context) => {
  const { action, id, data, reportData } = event;
  const wxContext = cloud.getWXContext();
  const openid = wxContext.OPENID;
  
  console.log('VIP咨询请求', { action, id, openid });
  
  switch (action) {
    case 'list':
      return await getConsultList(openid);
    case 'submit':
      return await submitConsult(data, openid);
    case 'detail':
      return await getConsultDetail(id, openid);
    case 'save-report':
      return await saveReport(id, reportData, openid);
    case 'delete':
      return await deleteConsult(id, openid);
    default:
      return {
        success: false,
        message: '未知操作'
      };
  }
};

// 获取咨询列表
async function getConsultList(openid) {
  try {
    const result = await db.collection('vip_consults')
      .where({
        openid: openid
      })
      .orderBy('createdAt', 'desc')
      .get();
    
    return {
      success: true,
      data: result.data
    };
  } catch (error) {
    console.error('获取列表失败', error);
    return {
      success: false,
      message: '获取失败'
    };
  }
}

// 提交咨询
async function submitConsult(data, openid) {
  try {
    const consultId = generateConsultId();
    
    await db.collection('vip_consults').add({
      consultId: consultId,
      openid: openid,
      ...data,
      status: 'pending', // pending, in_progress, completed
      reportData: null,
      createdAt: new Date(),
      updatedAt: new Date()
    });
    
    return {
      success: true,
      id: consultId,
      message: '咨询已提交'
    };
  } catch (error) {
    console.error('提交咨询失败', error);
    return {
      success: false,
      message: '提交失败'
    };
  }
}

// 获取咨询详情
async function getConsultDetail(consultId, openid) {
  try {
    const result = await db.collection('vip_consults')
      .where({
        consultId: consultId,
        openid: openid
      })
      .get();
    
    if (result.data.length === 0) {
      return {
        success: false,
        message: '咨询不存在'
      };
    }
    
    return {
      success: true,
      data: result.data[0]
    };
  } catch (error) {
    console.error('获取详情失败', error);
    return {
      success: false,
      message: '获取失败'
    };
  }
}

// 保存报告
async function saveReport(consultId, reportData, openid) {
  try {
    const result = await db.collection('vip_consults')
      .where({
        consultId: consultId,
        openid: openid
      })
      .get();
    
    if (result.data.length === 0) {
      return {
        success: false,
        message: '咨询不存在'
      };
    }
    
    await db.collection('vip_consults')
      .doc(result.data[0]._id)
      .update({
        reportData: reportData,
        status: 'completed',
        updatedAt: new Date()
      });
    
    return {
      success: true,
      message: '保存成功'
    };
  } catch (error) {
    console.error('保存报告失败', error);
    return {
      success: false,
      message: '保存失败'
    };
  }
}

// 删除咨询
async function deleteConsult(consultId, openid) {
  try {
    const result = await db.collection('vip_consults')
      .where({
        consultId: consultId,
        openid: openid
      })
      .get();
    
    if (result.data.length === 0) {
      return {
        success: false,
        message: '咨询不存在'
      };
    }
    
    await db.collection('vip_consults')
      .doc(result.data[0]._id)
      .remove();
    
    return {
      success: true,
      message: '删除成功'
    };
  } catch (error) {
    console.error('删除失败', error);
    return {
      success: false,
      message: '删除失败'
    };
  }
}

// 生成咨询ID
function generateConsultId() {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8).toUpperCase();
  return `VIP_${timestamp}_${random}`;
}
