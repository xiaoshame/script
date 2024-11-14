// 设置每天执行一次的定时任务
chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create('fetchData', {
    periodInMinutes: 480 // 8小时
  });
  checkAndFetchData(); // 首次安装时检查并获取数据
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'fetchData') {
    checkAndFetchData();
  }
});

// 消息监听器
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'checkAndFetchData') {
    checkAndFetchData();
  }
});
function checkAndFetchData() {
  const today = new Date();
  const formattedDate = today.toISOString().split('T')[0];

  chrome.storage.local.get(['scoreHistory'], function (result) {
    const history = result.scoreHistory || [];
    const lastRecord = history[history.length - 1];
    if (!lastRecord || lastRecord.date !== formattedDate) {
      fetchAndStoreData(formattedDate);
    }
  });
}

function fetchAndStoreData(formattedDate) {
  fetch(`https://production.dataviz.cnn.io/index/fearandgreed/graphdata/${formattedDate}`)
    .then(response => response.json())
    .then(jsonData => {
      const fearGreedScore = jsonData.fear_and_greed.score;
      const momentumScore = jsonData.market_momentum_sp500.score;
      // 获取已存储的数据
      chrome.storage.local.get(['scoreHistory'], function (result) {
        let history = result.scoreHistory || [];
        // 添加新数据
        history.push({
          date: formattedDate,
          fearGreedScore: fearGreedScore,
          momentumScore: momentumScore,
        });

        // 只保留最近15天的数据
        if (history.length > 15) {
          history = history.slice(-15);
        }

        // 存储更新后的数据
        chrome.storage.local.set({
          scoreHistory: history
        });


      });
    })
    .catch(error => console.error('Error fetching data:', error));
}
