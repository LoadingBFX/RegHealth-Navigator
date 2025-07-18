import React from 'react';
import { ComparisonStats as ComparisonStatsType } from '../../services/api';
import { BarChart3, FileText, GitCompare, Database } from 'lucide-react';

interface Props {
  stats: ComparisonStatsType;
}

const ComparisonStats: React.FC<Props> = ({ stats }) => {
  const statItems = [
    {
      label: 'Sections Compared',
      value: stats.total_sections_compared,
      icon: GitCompare,
      color: 'bg-blue-100 text-blue-600',
      description: 'Sections found in both documents'
    },
    {
      label: 'Document A Unique Sections',
      value: stats.rule1_unique_sections,
      icon: FileText,
      color: 'bg-purple-100 text-purple-600',
      description: 'Sections only in first document'
    },
    {
      label: 'Document B Unique Sections', 
      value: stats.rule2_unique_sections,
      icon: FileText,
      color: 'bg-green-100 text-green-600',
      description: 'Sections only in second document'
    }
  ];

  const totalSections = stats.total_sections_compared + stats.rule1_unique_sections + stats.rule2_unique_sections;
  const comparisonRate = totalSections > 0 ? (stats.total_sections_compared / totalSections * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {statItems.map((item, index) => (
          <div 
            key={index}
            className="bg-white border rounded-lg p-4 text-center hover:shadow-md transition-shadow"
          >
            <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg ${item.color} mb-3`}>
              <item.icon className="h-5 w-5" />
            </div>
            <div className="text-2xl font-bold text-gray-800 mb-1">
              {item.value.toLocaleString()}
            </div>
            <div className="text-xs text-gray-600 leading-tight mb-1">
              {item.label}
            </div>
            <div className="text-xs text-gray-500">
              {item.description}
            </div>
          </div>
        ))}
      </div>

      {/* Analysis Insights */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center mb-3">
          <BarChart3 className="h-4 w-4 text-gray-600 mr-2" />
          <h4 className="font-medium text-gray-800">Analysis Insights</h4>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="bg-white p-3 rounded border">
            <div className="font-medium text-blue-600 mb-1">Coverage Rate</div>
            <div className="text-2xl font-bold text-gray-800">
              {comparisonRate.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-600">
              Sections found in both documents
            </div>
          </div>
          
          <div className="bg-white p-3 rounded border">
            <div className="font-medium text-green-600 mb-1">Unique Content</div>
            <div className="text-2xl font-bold text-gray-800">
              {((stats.rule1_unique_sections + stats.rule2_unique_sections) / totalSections * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-600">
              Sections unique to one document
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};

export default ComparisonStats;