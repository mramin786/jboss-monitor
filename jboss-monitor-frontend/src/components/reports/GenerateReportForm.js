import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FaFilePdf, FaFileCsv } from 'react-icons/fa';
import LoadingSpinner from '../common/LoadingSpinner';

const GenerateReportForm = () => {
  const navigate = useNavigate();
  const [environment, setEnvironment] = useState('non_production');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [format, setFormat] = useState('pdf');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`/api/reports/${environment}/generate`, {
        username,
        password,
        format
      });

      if (response.status === 201) {
        // Redirect to reports page
        navigate('/reports');
      }
    } catch (err) {
      console.error('Error generating report:', err);
      setError(
        err.response?.data?.message || 
        'Failed to generate report. Please check your credentials and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-semibold mb-6">Generate JBoss Status Report</h2>
      
      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4" role="alert">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="environment">
            Environment
          </label>
          <select
            id="environment"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            value={environment}
            onChange={(e) => setEnvironment(e.target.value)}
            required
          >
            <option value="production">Production</option>
            <option value="non_production">Non-Production</option>
          </select>
        </div>

        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="username">
            JBoss Username
          </label>
          <input
            id="username"
            type="text"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="Enter JBoss username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>

        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
            JBoss Password
          </label>
          <input
            id="password"
            type="password"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="Enter JBoss password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-gray-700 text-sm font-bold mb-2">
            Report Format
          </label>
          <div className="flex">
            <div 
              className={`mr-4 p-3 border rounded-lg cursor-pointer flex items-center ${format === 'pdf' ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}`}
              onClick={() => setFormat('pdf')}
            >
              <FaFilePdf className="text-red-600 mr-2" size={20} />
              <span>PDF</span>
            </div>
            <div 
              className={`p-3 border rounded-lg cursor-pointer flex items-center ${format === 'csv' ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}`}
              onClick={() => setFormat('csv')}
            >
              <FaFileCsv className="text-green-600 mr-2" size={20} />
              <span>CSV</span>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <button
            type="button"
            className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
            onClick={() => navigate('/reports')}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline flex items-center"
            disabled={loading}
          >
            {loading ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Generating...
              </>
            ) : (
              'Generate Report'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default GenerateReportForm;
