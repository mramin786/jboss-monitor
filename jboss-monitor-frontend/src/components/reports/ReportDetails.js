import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { format } from 'date-fns';
import { FaDownload, FaArrowLeft, FaFilePdf, FaFileCsv } from 'react-icons/fa';
import StatusBadge from '../common/StatusBadge';
import LoadingSpinner from '../common/LoadingSpinner';

const ReportDetails = () => {
  const { reportId } = useParams();
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Function to fetch report details
  const fetchReport = async () => {
    try {
      const response = await axios.get(`/api/reports/${reportId}`);
      if (response.status === 200) {
        setReport(response.data);
        setError(null);
      }
    } catch (err) {
      console.error('Error fetching report details:', err);
      setError('Failed to fetch report details. The report may have been deleted.');
    } finally {
      setLoading(false);
    }
  };

  // Fetch report details on component mount and periodically if report is generating
  useEffect(() => {
    fetchReport();
    
    // Set up polling if report is generating
    let interval;
    if (report && report.status === 'generating') {
      interval = setInterval(() => {
        fetchReport();
      }, 3000); // Check every 3 seconds
    }
    
    // Clean up interval on component unmount or when report status changes
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [reportId, report?.status]);

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
        return <FaFilePdf className="text-red-600" size={24} />;
      case 'csv':
        return <FaFileCsv className="text-green-600" size={24} />;
      default:
        return null;
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto p-4">
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4" role="alert">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
        <button
          onClick={() => navigate('/reports')}
          className="flex items-center text-blue-600 hover:text-blue-800"
        >
          <FaArrowLeft className="mr-2" />
          Back to Reports
        </button>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="max-w-3xl mx-auto p-4">
        <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4" role="alert">
          <p className="font-bold">Report Not Found</p>
          <p>The requested report could not be found.</p>
        </div>
        <button
          onClick={() => navigate('/reports')}
          className="flex items-center text-blue-600 hover:text-blue-800"
        >
          <FaArrowLeft className="mr-2" />
          Back to Reports
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <button
          onClick={() => navigate('/reports')}
          className="flex items-center text-blue-600 hover:text-blue-800"
        >
          <FaArrowLeft className="mr-2" />
          Back to Reports
        </button>
        
        {report.status === 'completed' && (
          <a 
            href={`/api/reports/${report.id}/download`}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            target="_blank"
            rel="noopener noreferrer"
          >
            <FaDownload className="mr-2" />
            Download Report
          </a>
        )}
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Report Details
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              JBoss status report information
            </p>
          </div>
          <div className="flex items-center">
            {getFormatIcon(report.format)}
            <span className="ml-2 text-sm font-medium text-gray-500">{report.format.toUpperCase()}</span>
          </div>
        </div>
        <div className="border-t border-gray-200">
          <dl>
            <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Report ID</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{report.id}</dd>
            </div>
            <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Environment</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {report.environment.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </dd>
            </div>
            <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Created By</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{report.created_by}</dd>
            </div>
            <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Created At</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{formatDate(report.created_at)}</dd>
            </div>
            <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                <StatusBadge 
                  status={
                    report.status === 'completed' ? 'up' : 
                    report.status === 'generating' ? 'pending' : 
                    'down'
                  } 
                  text={report.status.toUpperCase()} 
                />
              </dd>
            </div>
            {report.completed_at && (
              <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500">Completed At</dt>
                <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{formatDate(report.completed_at)}</dd>
              </div>
            )}
            {report.error && (
              <div className="bg-red-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-red-500">Error</dt>
                <dd className="mt-1 text-sm text-red-700 sm:mt-0 sm:col-span-2">{report.error}</dd>
              </div>
            )}
          </dl>
        </div>
      </div>

      {report.status === 'generating' && (
        <div className="mt-6 flex justify-center">
          <div className="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4" role="alert">
            <div className="flex items-center">
              <LoadingSpinner size="sm" className="mr-2" />
              <p>Report generation in progress. This page will update automatically when complete.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportDetails;
