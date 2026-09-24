"use client"

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';
import { FileText, RefreshCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import DocumentUploadDialog from '@/components/admin/document-upload-dialog';

export default function DocumentManagerPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await apiClient.fetchWithAuth('/admin/documents');
      if (Array.isArray(data)) {
        setDocuments(data);
      } else {
        setDocuments([]);
      }
    } catch (e: any) {
      setError(e.message || "Failed to fetch documents");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container max-w-[1400px] py-8 space-y-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Document Manager</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage insurance policies in the agentic knowledge base
          </p>
        </div>
      </div>

      <Card className="border shadow-sm">
        <div className="flex flex-col sm:flex-row items-center justify-between p-4 border-b gap-4 bg-card/50">
          <div className="text-sm text-muted-foreground font-medium flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Uploaded Policies
          </div>
          <div className="flex gap-2 w-full sm:w-auto">
            <Button 
              onClick={fetchDocuments}
              variant="outline"
              size="sm"
              className="h-9 w-full sm:w-auto"
            >
              <RefreshCcw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <DocumentUploadDialog onUploadSuccess={fetchDocuments} />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b">
              <tr>
                <th className="px-6 py-3 font-medium">Document Name</th>
                <th className="px-6 py-3 font-medium">Type</th>
                <th className="px-6 py-3 font-medium">Version</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Ingested At</th>
                <th className="px-6 py-3 font-medium">Errors</th>
              </tr>
            </thead>
            <tbody>
              {loading && documents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-muted-foreground">
                    <div className="flex justify-center items-center gap-2">
                      <RefreshCcw className="h-4 w-4 animate-spin" />
                      Loading documents...
                    </div>
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-destructive">
                    {error}
                  </td>
                </tr>
              ) : documents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-muted-foreground">
                    No documents found. Upload an insurance policy to get started.
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id} className="border-b hover:bg-muted/30 transition-colors">
                    <td className="px-6 py-4 font-medium text-foreground">{doc.document_name}</td>
                    <td className="px-6 py-4 text-muted-foreground">{doc.document_type || '—'}</td>
                    <td className="px-6 py-4 text-muted-foreground">{doc.version || '—'}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <div className={`h-2 w-2 rounded-full ${
                          doc.status === 'COMPLETED' ? 'bg-green-500' : 
                          doc.status === 'FAILED' ? 'bg-destructive' : 
                          doc.status === 'PROCESSING' ? 'bg-blue-500' : 'bg-amber-500'
                        }`} />
                        <span className="text-xs font-medium capitalize">{doc.status?.toLowerCase()}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-muted-foreground text-xs font-mono whitespace-nowrap">
                      {doc.ingestion_timestamp ? new Date(doc.ingestion_timestamp).toLocaleString() : '—'}
                    </td>
                    <td className="px-6 py-4 text-destructive text-xs truncate max-w-[200px]" title={doc.error_message}>
                      {doc.error_message || '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
