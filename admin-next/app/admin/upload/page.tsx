'use client';
import { useState, useEffect } from 'react';
import { uploadFile, getFiles, deleteFile, updateFileStatus, KBFile } from '@/lib/api';

export default function UploadPage() {
  const [file, setFile]     = useState<File | null>(null);
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState<KBFile[]>([]);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    loadFiles();
  }, []);

  async function loadFiles() {
    setFetching(true);
    try {
      const d = await getFiles();
      setFiles(d.files);
    } catch (e) { console.error(e); }
    setFetching(false);
  }

  async function upload() {
    if (!file) { alert('Fayl tanlang!'); return; }
    setLoading(true); setStatus('⏳ Yuklanmoqda...');
    try {
      const d = await uploadFile(file);
      setLoading(false);
      if (d.ok) {
        setStatus(`✅ Yuklandi: ${d.filename} (${d.pairs} Q&A)`);
        setFile(null);
        loadFiles();
      } else {
        setStatus(`❌ Xatolik: ${d.error}`);
      }
    } catch {
      setLoading(false);
      setStatus('❌ Serverga ulanib bo\'lmadi.');
    }
  }

  async function remove(filename: string) {
    if (!confirm(`Haqiqatdan ham "${filename}" faylini o'chirmoqchimisiz?`)) return;
    try {
      const d = await deleteFile(filename);
      if (d.ok) loadFiles();
      else alert(`Xatolik: ${d.error}`);
    } catch (e) { alert('Serverga ulanishda xatolik'); }
  }

  async function toggleStatus(filename: string, current: string) {
    const next = current === 'trained' ? 'draft' : 'trained';
    try {
      const d = await updateFileStatus(filename, next);
      if (d.ok) loadFiles();
      else alert(`Xatolik: ${d.error}`);
    } catch { alert('Serverga ulanishda xatolik'); }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Bilimlar bazasi</div>
          <div className="page-sub">AI o&#39;rganishi uchun yangi hujjatlar yuklang va mavjudlarini boshqaring</div>
        </div>
      </div>

      <div className="grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32, alignItems: 'start' }}>
        
        {/* Upload Column */}
        <section>
          <div className="section-title">Yangi hujjat qo'shish</div>
          <div className="card">
            <div 
              className={`dropzone ${dragActive ? 'active' : ''}`}
              onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}
              onClick={() => document.getElementById('file-inp')?.click()}
            >
              <div className="dropzone-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
              </div>
              <div className="dropzone-text">
                {file ? <span style={{ color: 'var(--indigo)', fontWeight: 700 }}>{file.name}</span> : <span>Faylni bu yerga tashlang yoki tanlash uchun bosing</span>}
              </div>
              <div className="dropzone-hint">PDF, DOCX, XLSX, TXT, MD formatlari (Max: 10MB)</div>
              <input 
                id="file-inp" type="file" style={{ display: 'none' }} 
                onChange={e => setFile(e.target.files?.[0] ?? null)} 
              />
            </div>

            <div style={{ marginTop: 24 }}>
              <button 
                className="btn btn-primary" style={{ width: '100%', padding: '14px' }}
                onClick={upload} disabled={loading || !file}
              >
                {loading ? 'Yuklanmoqda...' : 'Yuklashni boshlash'}
              </button>
            </div>

            {status && (
              <div style={{ 
                marginTop: 20, padding: '14px', borderRadius: '12px', fontSize: 13, fontWeight: 500,
                background: status.startsWith('✅') ? '#ecfdf5' : '#fff1f2',
                color: status.startsWith('✅') ? '#065f46' : '#991b1b',
                border: `1px solid ${status.startsWith('✅') ? '#10b98130' : '#ef444430'}`
              }}>
                {status}
              </div>
            )}
          </div>
        </section>

        {/* List Column */}
        <section>
          <div className="section-title">Mavjud hujjatlar ({files.length})</div>
          <div className="table-card" style={{ margin: 0, minHeight: 400 }}>
            <table style={{ minWidth: '100%' }}>
              <thead>
                <tr>
                  <th>Fayl nomi</th>
                  <th>Hajmi</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Amallar</th>
                </tr>
              </thead>
              <tbody>
                {fetching ? (
                  Array(5).fill(0).map((_, i) => (
                    <tr key={i}>
                      <td colSpan={3}><div className="skeleton" style={{ height: 20, margin: '10px 0' }} /></td>
                    </tr>
                  ))
                ) : files.length === 0 ? (
                  <tr>
                    <td colSpan={3} style={{ textAlign: 'center', padding: '100px 0', color: 'var(--muted2)' }}>
                      Hali hech qanday fayl yuklanmagan
                    </td>
                  </tr>
                ) : (
                  files.map(f => (
                    <tr key={f.name}>
                      <td style={{ fontWeight: 600 }}>{f.name}</td>
                      <td style={{ color: 'var(--muted)', fontSize: 12 }}>{formatSize(f.size)}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span className={`badge ${f.status === 'trained' ? 'badge-blue' : 'badge-red'}`} style={{ fontSize: 10 }}>
                            {f.status === 'trained' ? 'Trained' : 'Draft'}
                          </span>
                          <button 
                            className="btn btn-sm" 
                            onClick={() => toggleStatus(f.name, f.status)}
                            style={{ padding: '2px 6px', fontSize: 10, background: '#f8fafc', border: '1px solid #e2e8f0' }}
                          >
                            {f.status === 'trained' ? 'Draftga' : 'O\'qitish'}
                          </button>
                        </div>
                        <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>{f.pairs} pairs</div>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button 
                          className="btn btn-red btn-sm" 
                          onClick={() => remove(f.name)}
                          title="O'chirish"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

      </div>
    </>
  );
}
