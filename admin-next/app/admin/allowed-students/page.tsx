'use client';
import { useState, useEffect } from 'react';
import { getApiUrl, getToken } from '@/lib/api';

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
      const res = await fetch(`${getApiUrl()}/api/admin/allowed-students`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (res.ok) {
        const data = await res.json();
        setStudents(data.students || []);
      }
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
      const res = await fetch(`${getApiUrl()}/api/admin/allowed-students/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` },
        body: formData
      });
      
      const data = await res.json();
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
    <div className="p-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 mb-2">Talabalar Bazasi</h1>
        <p className="text-slate-500">Botdan ro'yxatdan o'ta oladigan talabalar ro'yxatini Excel (.xlsx) orqali yuklang.</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-8 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Yangi ro'yxat yuklash (.xlsx)</h2>
        <div className="flex items-center gap-4">
          <input 
            type="file" 
            accept=".xlsx"
            onChange={e => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-slate-500
              file:mr-4 file:py-2.5 file:px-4
              file:rounded-xl file:border-0
              file:text-sm file:font-semibold
              file:bg-indigo-50 file:text-indigo-700
              hover:file:bg-indigo-100 transition-colors"
          />
          <button 
            className="btn btn-primary whitespace-nowrap" 
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? 'Yuklanmoqda...' : 'Yuklash'}
          </button>
        </div>
        {status && <div className="mt-4 text-sm font-medium">{status}</div>}
        <p className="text-xs text-slate-400 mt-4">
          * Excel faylning birinchi qatori sarlavha bo'lishi kerak. ID ustuni "ID" yoki "PINFL", ism ustuni "Name" yoki "F.I.O" so'zlarini o'z ichiga olishi kerak. (Yoki avtomatik 1-ustun ID, 2-ustun ism deb qabul qilinadi).
          <br/>* Diqqat: Yangi fayl yuklash orqali avvalgi barcha ro'yxat tozalanib, faqat yangi fayldagi talabalar qoladi.
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h2 className="font-semibold text-slate-800">Joriy bazadagi talabalar</h2>
          <span className="badge badge-blue">{students.length} ta talaba</span>
        </div>
        
        {loading ? (
          <div className="p-8 text-center text-slate-400">Yuklanmoqda...</div>
        ) : students.length === 0 ? (
          <div className="p-8 text-center text-slate-400">Hozircha hech qanday talaba ro'yxatga olinmagan.</div>
        ) : (
          <div className="max-h-[500px] overflow-y-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-500 uppercase bg-slate-50 sticky top-0">
                <tr>
                  <th className="px-6 py-3 font-semibold">Talaba ID</th>
                  <th className="px-6 py-3 font-semibold">F.I.O</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {students.map((s, i) => (
                  <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-3 font-medium text-slate-900">{s.student_id}</td>
                    <td className="px-6 py-3 text-slate-600">{s.full_name || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
