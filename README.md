# Serenity 觀點追蹤

追 X 帳號 @aleabitoreddit（Serenity）的公開貼文，AI 判讀每則提到哪些股票、看多看空，產出一頁 index.html。

## 檔案
- data/tweets_raw.json：抓下來的原始貼文
- data/classified.json：加上 AI 標籤（增量，已標過的不重跑）
- classify.py：用 claude CLI 標籤，不用 API key。`python3 classify.py sonnet`
- build.py：產 index.html
- fetch_x.js：在已登入 X 的 Chrome，開 x.com/aleabitoreddit，貼到 console 執行，再送回 receiver.py
- receiver.py：本機收資料。`python3 receiver.py data/incoming.json`，收到後把 incoming 合併進 tweets_raw

## 更新流程（目前半自動）
1. 開 Chrome 到 x.com/aleabitoreddit（要登入）
2. 跑 fetch_x.js，再導到 http://127.0.0.1:8765/receive#... 送回
3. python3 merge.py && python3 classify.py && python3 build.py

## 已知限制
- 「Subscribe to unlock」的付費貼文只看得到開頭，標記 paywalled
- 全自動要靠 bb-browser 的專用瀏覽器登入 X 一次，之後可排程
