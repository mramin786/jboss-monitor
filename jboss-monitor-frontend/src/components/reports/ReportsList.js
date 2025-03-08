import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { Link } from 'react-router-dom';
import { FaFilePdf, FaFileCsv, FaDownload, FaTrash } from 'react-icons/fa';
import axios from 'axios';
import StatusBadge from '../common/StatusBadge';
import LoadingSpinner from '../common/LoadingSpinner';

const ReportsList = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingReport, setDeletingReport] = useState(null);

  // Function to fetch reports
  const fetchReports = async () => {
    try {
      const response = await axios.get('/api/reports/');
      if (response.status === 200) {
        setReports(response.data);
        // Only clear error if we get actual data
        if (response.data && Array.isArray(response.data)) {
          setError(null);
        }
      }
    } catch (err) {
      console.error("Error fetching reports:", err);
      // Only set error if we don't have any reports already
      if (!reports.length) {
        setError('Failed to fetch reports');
      }
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchReports();
    
    // Set up polling to refresh report status
    const interval = setInterval(() => {
      fetchReports();
    }, 5000); // Refresh every 5 seconds
    
    // Clean up interval on component unmount
    return () => clearInterval(interval);
  }, []);

  // Handle report deletion
  const handleDeleteReport = async (reportId) => {
    if (!window.confirm('Are you sure you want to delete this report?')) {
      return;
    }
    
    setDeletingReport(reportId);
    
    try {
      const response = await axios.delete(`/api/reports/${reportId}`);
      if (response.status === 200) {
        // Remove the deleted report from state
        setReports(reports.filter(report => report.id !== reportId));
      }
    } catch (err) {
      console.error('Error deleting report:', err);
      alert('Failed to delete the report. Please try again.');
    } finally {
      setDeletingReport(null);
    }
  };

  // Format report status for display
  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return <StatusBadge status="up" text="COMPLETED" />;
      case 'generating':
        return <StatusBadge status="pending" text="GENERATING" />;
      case 'failed':
        return <StatusBadge status="down" text="FAILED" />;
      default:
        return <StatusBadge status="unknown" text="UNKNOWN" />;
    }
  };

  // Format date for display
  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return format(date, 'MM/dd/yyyy, hh:mm:ss a');
    } catch (error) {
      return dateString || 'Unknown';
    }
  };

  // Get icon for report format
  const getFormatIcon = (format) => {
    switch (format) {
      case 'pdf':
        return <FaFilePdf className="text-red-600" />;
      case 'csv':
        return <FaFileCsv className="text-green-600" />;
      default:
        return null;
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="container mx-auto px-4">
      {error && !reports.length && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4" role="alert">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      )}

      {reports.length === 0 && !loading ? (
        <div className="text-center py-8">
          <h3 className="text-xl font-medium text-gray-700">No Reports Yet</h3>
          <p className="text-gray-500 mt-2">
            Generate your first JBoss status report by clicking the button below.
          </p>
          <Link 
            to="/reports/generate" 
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Generate Report
          </Link>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border border-gray-200">
            <thead className="bg-gray-800 text-white">
              <tr>
                <th className="py-3 px-4 text-left">Environment</th>
                <th className="py-3 px-4 text-left">Format</th>
                <th className="py-3 px-4 text-left">Created At</th>
                <th className="py-3 px-4 text-left">Status</th>
                <th className="py-3 px-4 text-left">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {reports.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50">
                  <td className="py-3 px-4 flex items-center">
                    <span className="ml-2">{report.environment.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                  </td>
                  <td className="py-3 px-4 flex items-center">
                    {getFormatIcon(report.format)}
                    <span className="ml-2">{report.format.toUpperCase()}</span>
                  </td>
                  <td className="py-3 px-4">{formatDate(report.created_at)}</td>
                  <td className="py-3 px-4">{getStatusBadge(report.status)}</td>
                  <td className="py-3 px-4 flex space-x-2">
                    {report.status === 'completed' && (
                      <a 
                        href={`/api/reports/${report.id}/download`}
                        className="text-blue-600 hover:text-blue-800"
                        title="Download"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <FaDownload />
                      </a>
                    )}
                    <button
                      onClick={() => handleDeleteReport(report.id)}
                      className="text-red-600 hover:text-red-800"
                      title="Delete"
                      disabled={deletingReport === report.id}
                    >
                      {deletingReport === report.id ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <FaTrash />
                      )}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ReportsList;
