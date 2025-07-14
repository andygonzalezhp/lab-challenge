import React, { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip } from "recharts";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";

dayjs.extend(relativeTime);

export default function App() {
  /* state */
  const [metric, setMetric]         = useState("hr");
  const [userId, setUserId]         = useState(1);
  const [start, setStart]           = useState("2024-01-01");
  const [end,   setEnd]             = useState("2024-01-07");

  const [data,        setData]        = useState([]);      // full line
  const [imputedData, setImputedData] = useState([]);      // red dots
  const [adherence,   setAdherence]   = useState(null);    // adherence cards
  const [plist,       setPlist]       = useState([]);      // sidebar list

  /* fetch participant list once */
  useEffect(() => {
    fetch("http://localhost:8000/participants")
      .then(r => r.json())
      .then(setPlist)
      .catch(console.error);
  }, []);

  /* helpers */
 const fetchData = async () => {
  const url = new URL("http://localhost:8000/data");
  url.searchParams.append("start_date", start);
  url.searchParams.append("end_date",   end);
  url.searchParams.append("metric",     metric);
  url.searchParams.append("user_id",    userId);

  const res = await fetch(url);
  if (!res.ok) { alert("API error loading data"); return; }

  const json = await res.json();

  const rows = json.timestamps.map((ts, i) => ({
    tsISO : ts,                               // keep raw iso for logic
    ts    : dayjs(ts).format("MM-DD HH:mm"),  // display label
    val   : json.values[i],
    imp   : json.imputed[i],
  }));

  const lastTrueIdx =
      [...rows].reverse().findIndex(r => !r.imp);
  const lastTruePos = lastTrueIdx === -1
      ? -1
      : rows.length - 1 - lastTrueIdx;

  const rowsWithDisplayFlag = rows.map((r, i) => ({
    ...r,
    showImp : r.imp && i > lastTruePos
  }));

  setData(rowsWithDisplayFlag);
  setImputedData(rowsWithDisplayFlag.filter(r => r.showImp));
};

  const fetchAdherence = async () => {
    const url = new URL("http://localhost:8000/adherence");
    url.searchParams.append("start_date", start);
    url.searchParams.append("end_date",   end);
    url.searchParams.append("user_id",    userId);

    const res = await fetch(url);
    if (!res.ok) { alert("API error loading adherence"); return; }
    setAdherence(await res.json());
  };

  const loadAll = () => {
    fetchData();
    fetchAdherence();
  };

  /* reload whenever parameters change */
  useEffect(() => { loadAll(); }, [userId, start, end, metric]);

  /* email helper */
  const sendEmail = async (reason) => {
    const body = { user_id:userId, start_date:start, end_date:end, reason };
    const res = await fetch("http://localhost:8000/notify", {
      method:"POST",
      headers:{ "Content-Type":"application/json" },
      body: JSON.stringify(body),
    });
    alert(res.ok ? "Email queued!" : "Failed to send email");
  };

  /*render*/
  return (
    <div style={{ padding:"2rem", fontFamily:"sans-serif" }}>
      <h2>Fitbit Dash – Task 4</h2>

      <div style={{ display:"flex" }}>
        {/* sidebar*/}
        <div style={{ minWidth:180, marginRight:"1rem" }}>
          <h4>Participants</h4>
          <ul style={{ listStyle:"none", padding:0 }}>
            {plist.map(p => (
              <li key={p.id}>
                <button
                  onClick={() => setUserId(p.id)}
                  style={{
                    width:"100%", textAlign:"left",
                    padding:"0.25rem 0.5rem",
                    background: p.id === userId ? "#eef" : "white",
                    border:"1px solid #ddd",
                    borderRadius:4, marginBottom:4, cursor:"pointer",
                  }}
                >
                  {p.name}
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* dashboard */}
        <div style={{ flex:1 }}>
          {/* controls */}
          <div style={{ marginBottom:"1rem" }}>
            <label>
              Metric:&nbsp;
              <select value={metric} onChange={e=>setMetric(e.target.value)}>
                {["hr","azm","br","hrv","spo2","activity"].map(m=>(
                  <option key={m} value={m}>{m.toUpperCase()}</option>
                ))}
              </select>
            </label>

            <label style={{ marginLeft:"1rem" }}>
              User:&nbsp;
              <input
                type="number"
                value={userId}
                onChange={e=>setUserId(+e.target.value)}
                style={{ width:"3rem" }}
              />
            </label>

            <label style={{ marginLeft:"1rem" }}>
              Start:&nbsp;
              <input type="date" value={start} onChange={e=>setStart(e.target.value)} />
            </label>

            <label style={{ marginLeft:"1rem" }}>
              End:&nbsp;
              <input type="date" value={end} onChange={e=>setEnd(e.target.value)} />
            </label>
          </div>

          {/* adherence cards */}
          {adherence && (
            <div style={{ display:"flex", gap:"1rem", marginBottom:"1.5rem" }}>
              <Card label="No Token"     value={adherence.no_token ? "Yes" : "No"} />
              <Card label="Last Upload"  value={dayjs(adherence.last_upload).fromNow()} />
              <Card label="Sleep Upload" value={`${adherence.sleep_upload_pct}%`}
                    warn={adherence.sleep_upload_pct < 70}
                    onWarnClick={() => sendEmail("Sleep upload < 70%")} />
              <Card label="Wear Time"    value={`${adherence.wear_time_pct}%`}
                    warn={adherence.wear_time_pct  < 70}
                    onWarnClick={() => sendEmail("Wear time < 70%")} />
            </div>
          )}

          {/* line + imputed dots */}
          <LineChart width={900} height={400} data={data}>
            <XAxis dataKey="ts" type="category" minTickGap={60}/>
            <YAxis />
            <Tooltip />

            <Line
              type="monotone"
              dataKey="val"
              stroke="#4287f5"
              strokeWidth={2}
              dot={({ cx, cy, payload }) =>
                payload.imp ? (
                  <circle cx={cx} cy={cy} r={6} fill="red" stroke="red" />
                ) : null
              }
            />
          </LineChart>
        </div>
      </div>
    </div>
  );
}

/* reusable card */
function Card({ label, value, warn=false, onWarnClick }) {
  return (
    <div style={{
      padding:"1rem",
      border:"1px solid #ccc",
      borderRadius:4,
      minWidth:140,
      textAlign:"center",
      background: warn ? "#fff4f4" : "white",
    }}>
      <strong>{label}:</strong><br/>{value}
      {warn && onWarnClick && (
        <div style={{ marginTop:"0.5rem" }}>
          <button onClick={onWarnClick} style={{ fontSize:"0.8rem" }}>
            Email&nbsp;participant
          </button>
        </div>
      )}
    </div>
  );
}
