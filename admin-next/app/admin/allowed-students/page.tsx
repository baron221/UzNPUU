'use client';
import { useState, useEffect } from 'react';
import { getAllowedStudents, uploadAllowedStudents } from '@/lib/api';

export default function AllowedStudentsPage() {
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState('');

  useEffect(() => {
    loadStudents();
  }, []);

  async function loadStudents() {
    setLoading(true);
    try {
      const data = await getAllowedStudents();
      setStudents(data.students || []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  }

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setStatus('Yuklanmoqda...');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const data = await uploadAllowedStudents(file);
      if (data.ok) {
        setStatus(`✅ Muvaffaqiyatli yuklandi: ${data.count} ta talaba.`);
        setFile(null);
        loadStudents();
      } else {
        setStatus(`❌ Xatolik: ${data.error}`);
      }
    } catch (e: any) {
      setStatus(`❌ Xatolik: ${e.message}`);
    }
    setUploading(false);
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Talabalar Bazasi</div>
          <div className="page-sub">Botdan ro'yxatdan o'ta oladigan talabalar ro'yxatini Excel (.xlsx) orqali yuklang.</div>
        </div>
      </div>

      <div className="table-card" style={{ padding: '24px', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text)', marginBottom: '16px' }}>Yangi ro'yxat yuklash (.xlsx)</h2>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <input 
            type="file" 
            accept=".xlsx"
            onChange={e => setFile(e.target.files?.[0] || null)}
            style={{ fontSize: '14px', cursor: 'pointer' }}
          />
          <button 
            className="btn btn-primary" 
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? 'Yuklanmoqda...' : 'Yuklash'}
          </button>
        </div>
        {status && <div style={{ marginTop: '16px', fontSize: '14px', fontWeight: 500 }}>{status}</div>}
        <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '16px', lineHeight: 1.5 }}>
          * Excel faylning birinchi qatori sarlavha bo'lishi kerak. ID ustuni "ID" yoki "PINFL", ism ustuni "Name" yoki "F.I.O" so'zlarini o'z ichiga olishi kerak. (Yoki avtomatik 1-ustun ID, 2-ustun ism deb qabul qilinadi).
          <br/>* Diqqat: Yangi fayl yuklash orqali avvalgi barcha ro'yxat tozalanib, faqat yangi fayldagi talabalar qoladi.
        </p>
      </div>

      <div className="table-card">
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #f1f2f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '15px', fontWeight: 600 }}>Joriy bazadagi talabalar</h2>
          <span className="badge badge-purple">{students.length} ta talaba</span>
        </div>
        
        {loading ? (
          <div style={{ padding: '32px', textAlign: 'center', color: 'var(--muted)' }}>Yuklanmoqda...</div>
        ) : students.length === 0 ? (
          <div style={{ padding: '32px', textAlign: 'center', color: 'var(--muted)' }}>Hozircha hech qanday talaba ro'yxatga olinmagan.</div>
        ) : (
          <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
            <table>
              <thead style={{ position: 'sticky', top: 0, background: 'var(--card)', zIndex: 1 }}>
                <tr>
                  <th style={{ width: '50px' }}>#</th>
                  <th>Talaba ID</th>
                  <th>F.I.O</th>
                </tr>
              </thead>
              <tbody>
                {students.map((s, i) => (
                  <tr key={i}>
                    <td style={{ color: 'var(--muted)', fontSize: '13px' }}>{i + 1}</td>
                    <td style={{ fontWeight: 500 }}>{s.student_id}</td>
                    <td style={{ color: 'var(--muted)' }}>{s.full_name || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
