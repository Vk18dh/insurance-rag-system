"use client"

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';
import { FileText, ArrowLeft, RefreshCw } from 'lucide-react';
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

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING': return <span className="bg-yellow-100 text-yellow-800 text-xs font-medium px-2.5 py-0.5 rounded border border-yellow-300">Pending</span>;
      case 'PROCESSING': return <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded border border-blue-300">Processing</span>;
      case 'COMPLETED': return <span className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded border border-green-300">Completed</span>;
      case 'FAILED': return <span className="bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded border border-red-300">Failed</span>;
      default: return <span>{status}</span>;
    }
  };

  return (
    <div className="container max-w-6xl py-8 space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <a href="/admin" className="text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-6 w-6" />
          </a>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Document Manager</h1>
            <p className="text-muted-foreground mt-1">
              Manage insurance policies in the agentic knowledge base.
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={fetchDocuments}
            className="outline-none inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <DocumentUploadDialog onUploadSuccess={fetchDocuments} />
        </div>
      </div>

      {error && <div className="p-4 bg-red-50 text-red-500 rounded border border-red-200">{error}</div>}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Uploaded Policies
          </CardTitle>
          <CardDescription>
            Documents are automatically chunked and indexed into ChromaDB and BM25 upon upload.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading && documents.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">Loading documents...</div>
          ) : documents.length === 0 ? (
            <div className="py-12 text-center border rounded-lg border-dashed">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium">No documents found</h3>
              <p className="text-sm text-muted-foreground mt-1">Upload an insurance policy PDF to get started.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left border-collapse">
                <thead className="text-xs uppercase bg-muted/50 border-b">
                  <tr>
                    <th className="px-6 py-3 font-medium">Document Name</th>
                    <th className="px-6 py-3 font-medium">Type</th>
                    <th className="px-6 py-3 font-medium">Version</th>
                    <th className="px-6 py-3 font-medium">Status</th>
                    <th className="px-6 py-3 font-medium">Ingested At</th>
                    <th className="px-6 py-3 font-medium">Errors</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-muted/50">
                      <td className="px-6 py-4 font-medium text-foreground">{doc.document_name}</td>
                      <td className="px-6 py-4 text-muted-foreground">{doc.document_type || '-'}</td>
                      <td className="px-6 py-4 text-muted-foreground">{doc.version || '-'}</td>
                      <td className="px-6 py-4">{getStatusBadge(doc.status)}</td>
                      <td className="px-6 py-4 text-muted-foreground whitespace-nowrap">
                        {doc.ingestion_timestamp ? new Date(doc.ingestion_timestamp).toLocaleString() : '-'}
                      </td>
                      <td className="px-6 py-4 text-red-500 text-xs truncate max-w-[200px]" title={doc.error_message}>
                        {doc.error_message || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
