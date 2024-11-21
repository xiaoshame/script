// 辅助函数：获取分数解释
function getScoreInterpretation(score) {
  if (score >= 0 && score <= 25) return 'Extreme Fear';
  if (score > 25 && score <= 45) return 'Fear';
  if (score > 45 && score <= 55) return 'Neutral';
  if (score > 55 && score <= 75) return 'Greed';
  if (score > 75 && score <= 100) return 'Extreme Greed';
  return 'Unknown';
}

// 比较指标函数
function compareIndicators(history) {
  const latest = history[history.length - 1];
  return {
    fearGreed: {
      current: latest.fearGreedScore,
      interpretation: getScoreInterpretation(latest.fearGreedScore)
    },
    momentum: {
      current: latest.momentumScore,
      interpretation: getScoreInterpretation(latest.momentumScore)
    }
  };
}

// 导出数据函数
function exportData(history) {
  const csvContent = "data:text/csv;charset=utf-8,"
    + "Date,Fear & Greed Score,Market Momentum Score\n"
    + history.map(item => `${item.date},${item.fearGreedScore},${item.momentumScore}`).join("\n");

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", "market_indicators.csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// 统计函数
function calculateStats(history) {
  return {
    fearGreed: {
      avg: average(history.map(h => h.fearGreedScore)),
      max: Math.max(...history.map(h => h.fearGreedScore)),
      min: Math.min(...history.map(h => h.fearGreedScore))
    },
    momentum: {
      avg: average(history.map(h => h.momentumScore)),
      max: Math.max(...history.map(h => h.momentumScore)),
      min: Math.min(...history.map(h => h.momentumScore))
    }
  };
}

function average(arr) {
  return (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(1);
}

// 更新统计数据显示函数
function updateStatistics(stats) {
  // Fear & Greed Index 统计
  document.getElementById('fearGreedAvg').textContent = `${stats.fearGreed.avg}`;
  document.getElementById('fearGreedMax').textContent = `${stats.fearGreed.max} (${getScoreInterpretation(stats.fearGreed.max)})`;
  document.getElementById('fearGreedMin').textContent = `${stats.fearGreed.min} (${getScoreInterpretation(stats.fearGreed.min)})`;

  // Market Momentum 统计
  document.getElementById('momentumAvg').textContent = `${stats.momentum.avg}`;
  document.getElementById('momentumMax').textContent = `${stats.momentum.max} (${getScoreInterpretation(stats.momentum.max)})`;
  document.getElementById('momentumMin').textContent = `${stats.momentum.min} (${getScoreInterpretation(stats.momentum.min)})`;
}

function checkAndFetchData() {
  return new Promise((resolve, reject) => {
    const today = new Date();
    const formattedDate = today.toISOString().split('T')[0];
    console.log('check and fetch data ' + formattedDate);
    chrome.storage.local.get(['scoreHistory'], async function (result) {
      const history = result.scoreHistory || [];
      const lastRecord = history[history.length - 1];
      if (!lastRecord || lastRecord.date !== formattedDate) {
        try{
          await fetchAndStoreData(formattedDate);
          resolve();
        }catch(error){
          reject(error);
        }
      }else{
        console.log('repeated requests');
        resolve();
      }
    });
  });
}

async function fetchAndStoreData(formattedDate) {
  try {
    const response = await fetch(`https://production.dataviz.cnn.io/index/fearandgreed/graphdata/${formattedDate}`);
    const jsonData = await response.json()
    console.log("execute fetchAndStoreData");
    const fearGreedScore = jsonData.fear_and_greed.score;
    const momentumScore = jsonData.market_momentum_sp500.score;
    // 获取已存储的数据
    chrome.storage.local.get(['scoreHistory'], async function (result) {
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
      console.log("set history length is " + history.length);
      // 存储更新后的数据
      await chrome.storage.local.set({
        scoreHistory: history
      });
    });
  }
  catch (error) {
    console.error('Error fetching data:', error);
  }
}

// 主要功能实现
document.addEventListener('DOMContentLoaded', function () {
  checkAndFetchData().then(() => {
    displayData();
  }).catch(error => {
    console.error('There was an error in checkAndFetchData:', error);
  });
});

function displayData() {
  chrome.storage.local.get(['scoreHistory'], function (result) {
    const history = result.scoreHistory || [];
    console.log('history length is ' + history.length);
    // 如果没有数据，显示提示信息
    if (history.length === 0) {
      document.body.innerHTML = '<p>No data available yet. Please wait for the first data collection.</p>';
      return;
    }

    // 更新当前状态显示
    const comparison = compareIndicators(history);
    document.getElementById('fearGreedStatus').textContent =
      `${comparison.fearGreed.current} (${comparison.fearGreed.interpretation})`;
    document.getElementById('momentumStatus').textContent =
      `${comparison.momentum.current} (${comparison.momentum.interpretation})`;

    // 计算并显示统计数据
    const stats = calculateStats(history);
    updateStatistics(stats);

    // 设置导出按钮事件
    document.getElementById('exportBtn').addEventListener('click', () => exportData(history));

    const dates = history.map(item => item.date);
    const fearGreedScores = history.map(item => item.fearGreedScore);
    const momentumScores = history.map(item => item.momentumScore);

    // 图表配置选项
    const chartOptions = {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          max: 100
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: function (context) {
              const score = context.raw;
              return `${context.dataset.label}: ${score} (${getScoreInterpretation(score)})`;
            }
          }
        }
      }
    };

    // 绘制 Fear & Greed Index 图表
    const fearGreedCtx = document.getElementById('fearGreedChart').getContext('2d');
    new Chart(fearGreedCtx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: [{
          label: 'Fear & Greed Index',
          data: fearGreedScores,
          borderColor: 'rgb(75, 192, 192)',
          tension: 0.1
        }]
      },
      options: chartOptions
    });

    // 绘制 Market Momentum 图表
    const momentumCtx = document.getElementById('momentumChart').getContext('2d');
    new Chart(momentumCtx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: [{
          label: 'Market Momentum (S&P500)',
          data: momentumScores,
          borderColor: 'rgb(255, 99, 132)',
          tension: 0.1
        }]
      },
      options: chartOptions
    });
  });
}
