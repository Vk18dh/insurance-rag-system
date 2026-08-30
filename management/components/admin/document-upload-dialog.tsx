"use client"

import React, { useState } from 'react';
import { Upload, X } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

export default function DocumentUploadDialog({ onUploadSuccess }: { onUploadSuccess: () => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [documentName, setDocumentName] = useState('');
  const [documentType, setDocumentType] = useState('Policy');
  const [source, setSource] = useState('');
  const [version, setVersion] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a PDF file.");
      return;
    }

    if (!documentName) {
      setError("Document name is required.");
      return;
    }

    try {
      setIsUploading(true);
      setError('');
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_name', documentName);
      if (documentType) formData.append('document_type', documentType);
      if (source) formData.append('source', source);
      if (version) formData.append('version', version);

      const token = localStorage.getItem('token');
      if (!token) throw new Error("Not authenticated");

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/documents`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || "Upload failed");
      }

      setIsOpen(false);
      onUploadSuccess();
      // Reset form
      setFile(null);
      setDocumentName('');
      setDocumentType('Policy');
      setSource('');
      setVersion('');

    } catch (e: any) {
      setError(e.message || "An error occurred during upload.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex items-center justify-center rounded-md text-sm font-medium h-10 px-4 py-2"
      >
        <Upload className="mr-2 h-4 w-4" />
        Upload Policy
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-background rounded-lg shadow-lg w-full max-w-md overflow-hidden border">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">Upload Policy Document</h2>
              <button 
                onClick={() => setIsOpen(false)}
                className="text-muted-foreground hover:text-foreground rounded-full p-1 hover:bg-muted"
                disabled={isUploading}
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <form onSubmit={handleUpload} className="p-4 space-y-4">
              {error && <div className="text-sm text-red-500 bg-red-50 p-2 rounded">{error}</div>}
              
              <div className="space-y-2">
                <label className="text-sm font-medium">PDF File *</label>
                <input 
                  type="file" 
                  accept="application/pdf"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                  disabled={isUploading}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Document Name *</label>
                <input 
                  type="text" 
                  value={documentName}
                  onChange={(e) => setDocumentName(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  placeholder="e.g., Motor Insurance Policy"
                  disabled={isUploading}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Type</label>
                  <input 
                    type="text" 
                    value={documentType}
                    onChange={(e) => setDocumentType(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    disabled={isUploading}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Version</label>
                  <input 
                    type="text" 
                    value={version}
                    onChange={(e) => setVersion(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    placeholder="e.g., v2.0"
                    disabled={isUploading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Source / Publisher</label>
                <input 
                  type="text" 
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder="e.g., IRDAI"
                  disabled={isUploading}
                />
              </div>

              <div className="pt-4 flex justify-end gap-2">
                <button 
                  type="button" 
                  onClick={() => setIsOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-muted rounded-md"
                  disabled={isUploading}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 rounded-md disabled:opacity-50 inline-flex items-center"
                  disabled={isUploading}
                >
                  {isUploading ? (
                    <>
                      <span className="animate-spin mr-2">⏳</span>
                      Uploading...
                    </>
                  ) : (
                    'Upload & Process'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
