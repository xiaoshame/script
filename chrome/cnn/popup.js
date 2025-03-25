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
    },
    vix:{
      current: latest.vixScore,
      interpretation: latest.vixTrend
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
    },
    vix: {
      avg: average(history.map(h => h.vixScore)),
      max: Math.max(...history.map(h => h.vixScore)),
      min: Math.min(...history.map(h => h.vixScore))
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
  
  // VIX统计
  document.getElementById('vixAvg').textContent = `${stats.vix.avg}`;
  document.getElementById('vixMax').textContent = `${stats.vix.max}`;
  document.getElementById('vixMin').textContent = `${stats.vix.min}`;
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
        fetchAndStoreData(formattedDate).then(resolve).catch(reject);
      } else {
        console.log('repeated requests');
        resolve();
      }
    });
  });
}

function fetchAndStoreData(formattedDate) {
  return new Promise(async (resolve, reject) => {
    try {
      // 获取Fear & Greed数据
      const response = await fetch(`https://production.dataviz.cnn.io/index/fearandgreed/graphdata/${formattedDate}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const jsonData = await response.json();
      const fearGreedScore = jsonData.fear_and_greed.score;
      const momentumScore = jsonData.market_momentum_sp500.score;

      // 获取VIX数据
      const vixResponse = await fetch('https://cn.investing.com/indices/volatility-s-p-500', {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
      });
      
      if (!vixResponse.ok) {
        throw new Error(`HTTP error! status: ${vixResponse.status}`);
      }
      
      const vixText = await vixResponse.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(vixText, 'text/html');
      const vixElement = doc.querySelector('dd[data-test="prevClose"] span.key-info_dd-numeric__ZQFIs span:nth-child(2)');
      const vixValue = vixElement ? parseFloat(vixElement.textContent) : null;
      // 获取趋势信息
      const trendElement = doc.querySelector('.mb-6.mt-1.rounded-full.text-center.font-semibold');
      const vixTrend = trendElement ? trendElement.textContent.trim() : '未知';

      // 获取已存储的数据
      chrome.storage.local.get(['scoreHistory'], function (result) {
        let history = result.scoreHistory || [];
        // 添加新数据
        history.push({
          date: formattedDate,
          fearGreedScore: fearGreedScore,
          momentumScore: momentumScore,
          vixScore: vixValue,
          vixTrend: vixTrend
        });

        // 只保留最近15天的数据
        if (history.length > 15) {
          history = history.slice(-15);
        }
        console.log("set history length is " + history.length);
        // 存储更新后的数据
        chrome.storage.local.set({ scoreHistory: history }, function () {
          if (chrome.runtime.lastError) {
            console.log("chrome.storage.local.set error");
            reject(chrome.runtime.lastError);
          } else {
            console.log("chrome.storage.local.set success");
            resolve();
          }
        });
      });
    }catch (error){
      console.error('Error fetching data:', error);
      throw(error);
    }
  });
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
      // 更新VIX状态显示
    document.getElementById('vixStatus').textContent = 
      `${comparison.vix.current} (${comparison.vix.interpretation})`;
    // 计算并显示统计数据
    const stats = calculateStats(history);
    updateStatistics(stats);

    // 设置导出按钮事件
    document.getElementById('exportBtn').addEventListener('click', () => exportData(history));

    const dates = history.map(item => item.date);
    const fearGreedScores = history.map(item => item.fearGreedScore);
    const momentumScores = history.map(item => item.momentumScore);
    const vixScores = history.map(item => item.vixScore);

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
              const label = context.dataset.label;
              // 根据不同的图表类型返回不同格式的tooltip
              if (label.includes('VIX')) {
                // VIX指数不需要解释函数
                return `${label}: ${score}`;
              } else {
                // Fear & Greed 和 Market Momentum 使用解释函数
                return `${label}: ${score} (${getScoreInterpretation(score)})`;
              }
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
    
    
    // 添加VIX图表
    const vixCtx = document.getElementById('vixChart').getContext('2d');
    new Chart(vixCtx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: [{
          label: 'VIX Index',
          data: vixScores,
          borderColor: 'rgb(153, 102, 255)',
          tension: 0.1
        }]
      },
      options: chartOptions
    });
  });
}
