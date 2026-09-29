import React, { useRef } from 'react';
import { UploadCloud, Image as ImageIcon, X, Camera, Loader2 } from 'lucide-react';

export default function ImageUploader({ files, setFiles, onAnalyze, loading }) {
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selected = Array.from(e.target.files);
    if (files.length + selected.length > 5) {
      alert('You can upload a maximum of 5 packaging photos.');
      return;
    }
    setFiles([...files, ...selected].slice(0, 5));
  };

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <UploadCloud className="h-5 w-5 text-emerald-600" />
            Upload Packaging Photos
          </h2>
          <p className="text-xs text-slate-500">
            Upload 1 to 5 photos (Front label, Nutrition panel, Ingredients, FSSAI logo, Dates).
          </p>
        </div>
        <span className="text-xs font-medium px-2.5 py-1 bg-slate-100 text-slate-700 rounded-full border border-slate-200">
          {files.length} / 5 photos
        </span>
      </div>

      {/* Dropzone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        className="border-2 border-dashed border-slate-300 hover:border-emerald-500 bg-slate-50 hover:bg-emerald-50/30 transition-all rounded-lg p-6 text-center cursor-pointer flex flex-col items-center justify-center gap-2"
      >
        <ImageIcon className="h-9 w-9 text-slate-400" />
        <p className="text-sm font-medium text-slate-700">
          Click or drag & drop packaging images here
        </p>
        <p className="text-xs text-slate-400">
          Supports PNG, JPG, JPEG, WEBP (Supports Hindi, Tamil, Telugu & English scripts)
        </p>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*"
          className="hidden"
          onChange={handleFileChange}
        />
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>

      {/* Mobile camera trigger */}
      <div className="mt-3 flex justify-end">
        <button
          type="button"
          onClick={() => cameraInputRef.current?.click()}
          className="text-xs text-slate-600 hover:text-emerald-700 font-medium flex items-center gap-1 px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 transition-colors"
        >
          <Camera className="h-3.5 w-3.5" />
          Take Photo with Camera
        </button>
      </div>

      {/* Thumbnails */}
      {files.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wider">
            Selected Images ({files.length}):
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {files.map((file, idx) => (
              <div
                key={idx}
                className="relative group rounded-lg overflow-hidden border border-slate-200 bg-slate-100 aspect-square flex items-center justify-center"
              >
                <img
                  src={URL.createObjectURL(file)}
                  alt={`Packaging ${idx + 1}`}
                  className="w-full h-full object-cover"
                />
                <button
                  type="button"
                  onClick={() => removeFile(idx)}
                  className="absolute top-1 right-1 bg-red-600 text-white rounded-full p-1 shadow-md opacity-90 hover:opacity-100 transition-opacity"
                  title="Remove image"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
                <span className="absolute bottom-1 left-1 bg-black/60 text-white text-[10px] px-1.5 py-0.5 rounded">
                  #{idx + 1}
                </span>
              </div>
            ))}
          </div>

          <div className="mt-4 flex justify-end">
            <button
              type="button"
              disabled={loading || files.length === 0}
              onClick={onAnalyze}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm px-5 py-2.5 rounded-lg shadow-sm transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Processing EasyOCR & Multi-Stage NLP...</span>
                </>
              ) : (
                <span>Analyze Packaging & Run FSSAI Audit</span>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
