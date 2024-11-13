// 设置每天执行一次的定时任务
chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create('fetchData', {
    periodInMinutes: 1440 // 24小时
  });
  fetchAndStoreData(); // 首次安装时立即执行一次
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'fetchData') {
    fetchAndStoreData();
  }
});

function fetchAndStoreData() {
  const today = new Date();
  const formattedDate = today.toISOString().split('T')[0];

  fetch(`https://production.dataviz.cnn.io/index/fearandgreed/graphdata/${formattedDate}`)
    .then(response => response.json())
    .then(jsonData => {
      const fearGreedScore = jsonData.fear_and_greed.score;
      const momentumScore = jsonData.market_momentum_sp500.score;
      // 获取已存储的数据
      chrome.storage.local.get(['scoreHistory'], function (result) {
        let history = result.scoreHistory || [];
        const todayExists = history.some(item => item.date === formattedDate);
        if (!todayExists) {
          // 添加新数据
          history.push({
            date: formattedDate,
            fearGreedScore: fearGreedScore,
            momentumScore: momentumScore,
          });

          // 只保留最近15天的数据
          if (history.length > 30) {
            history = history.slice(-30);
          }

          // 存储更新后的数据
          chrome.storage.local.set({
            scoreHistory: history
          });
        }

      });
    })
    .catch(error => console.error('Error fetching data:', error));
}
