import React, { useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip } from "recharts";
import dayjs from "dayjs";

export default function App() {
  const [metric, setMetric] = useState("hr");
  const [userId, setUserId] = useState(1);
  const [start, setStart] = useState("2024-01-01");
  const [end, setEnd] = useState("2024-01-07");
  const [data, setData] = useState([]);

  const fetchData = async () => {
    const url = new URL("http://localhost:8000/data");
    url.searchParams.append("start_date", start);
    url.searchParams.append("end_date", end);
    url.searchParams.append("metric", metric);
    url.searchParams.append("user_id", userId);

    const res = await fetch(url);
    if (!res.ok) return alert("API error");
    const json = await res.json();
    setData(json.timestamps.map((t, i) => ({
      ts: dayjs(t).format("MM-DD HH:mm"),
      val: json.values[i]
    })));
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h2>Fitbit Dash – Task 2</h2>
      <label>
        Metric:
        <select value={metric} onChange={e => setMetric(e.target.value)}>
          {["hr","azm","br","hrv","spo2","activity"].map(m => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </label>
      <label style={{ marginLeft: "1rem" }}>
        User:
        <input
          type="number"
          value={userId}
          onChange={e => setUserId(Number(e.target.value))}
          size="3"
        />
      </label>
      <br/><br/>
      <label>
        Start:
        <input
          type="date"
          value={start}
          onChange={e => setStart(e.target.value)}
        />
      </label>
      <label style={{ marginLeft: "1rem" }}>
        End:
        <input
          type="date"
          value={end}
          onChange={e => setEnd(e.target.value)}
        />
      </label>
      <button onClick={fetchData} style={{ marginLeft: "1rem" }}>Load</button>

      <LineChart width={900} height={400} data={data}>
        <XAxis dataKey="ts" minTickGap={60} />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="val" dot={false} />
      </LineChart>
    </div>
  );
}
