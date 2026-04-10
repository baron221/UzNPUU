'use client';
import { useState } from 'react';
import { uploadFile } from '@/lib/api';

export default function UploadPage() {
  const [file, setFile]     = useState<File | null>(null);
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);

  async function upload() {
    if (!file) { alert('Fayl tanlang!'); return; }
    setLoading(true); setStatus('⏳ Yuklanmoqda...');
    const d = await uploadFile(file);
    setLoading(false);
    if (d.ok) setStatus(`✅ Yuklandi: ${d.filename} (${d.pairs} Q&A)`);
    else setStatus(`❌ Xatolik: ${d.error}`);
  }

  return (
    <>
      <div className="page-header">
        <div><div className="page-title">Hujjat Yuklash</div><div className="page-sub">AI bilimlari bazasini boyitish</div></div>
      </div>

      <div className="info-box">
        📁 <strong>Qo&#39;llab-quvvatlanadigan formatlar:</strong> PDF, DOCX, XLSX, TXT, MD
        <br/>Yuklangan hujjatlar avtomatik AI tomonidan o&#39;rganiladi va talabalar savollariga javob berishda foydalaniladi.
      </div>

      <div className="card">
        <div className="section-title">Fayl tanlang</div>
        <div style={{ marginBottom: 20 }}>
          <input
            type="file"
            className="form-inp"
            accept=".pdf,.docx,.txt,.xlsx,.md"
            onChange={e => setFile(e.target.files?.[0] ?? null)}
            style={{ cursor: 'pointer' }}
          />
        </div>

        {file && (
          <div style={{ marginBottom:16, padding:'10px 14px', background:'#eef2ff', borderRadius:10, fontSize:13, color:'#4338ca', fontWeight:500 }}>
            📄 {file.name} ({(file.size / 1024).toFixed(1)} KB)
          </div>
        )}

        <button className="btn btn-primary" onClick={upload} disabled={loading || !file}>
          📤 {loading ? 'Yuklanmoqda...' : 'Yuklash'}
        </button>

        {status && (
          <div style={{ marginTop:16, fontSize:13, fontWeight:500, color: status.startsWith('✅') ? '#065f46' : status.startsWith('❌') ? '#991b1b' : '#4338ca' }}>
            {status}
          </div>
        )}
      </div>
    </>
  );
}
