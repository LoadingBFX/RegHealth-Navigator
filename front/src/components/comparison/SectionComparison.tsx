import React, { useState } from 'react';
import { SectionComparison as SectionComparisonType } from '../../services/api';
import { ChevronDown, ChevronUp, FileText, TrendingUp } from 'lucide-react';

interface Props {
  comparison: SectionComparisonType;
  index: number;
  rule1Name: string;
  rule2Name: string;
}

const SectionComparison: React.FC<Props> = ({ comparison, index, rule1Name, rule2Name }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getSimilarityColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getSimilarityLabel = (score: number) => {
    if (score >= 0.8) return 'High Similarity';
    if (score >= 0.6) return 'Medium Similarity';
    return 'Low Similarity';
  };

  return (
    <div className="border border-gray-200 rounded-lg bg-gray-50">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-100 rounded-t-lg"
      >
        <div className="flex items-center space-x-3">
          <span className="bg-blue-600 text-white text-sm font-medium px-2 py-1 rounded">
            #{index}
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-gray-800 truncate">
              {comparison.rule1_section}
            </p>
            <div className="flex items-center space-x-2 text-xs mt-1">
              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded font-medium">
                {rule1Name}
              </span>
              <span className="text-gray-400">vs</span>
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded font-medium">
                {rule2Name}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSimilarityColor(comparison.similarity_score)}`}>
            {getSimilarityLabel(comparison.similarity_score)} ({(comparison.similarity_score * 100).toFixed(0)}%)
          </span>
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-gray-500" />
          ) : (
            <ChevronDown className="h-4 w-4 text-gray-500" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 bg-white rounded-b-lg">
          {/* Metadata */}
          <div className="mb-4 flex items-center space-x-4 text-xs text-gray-600">
            <div className="flex items-center space-x-1">
              <TrendingUp className="h-3 w-3" />
              <span>Similarity: {(comparison.similarity_score * 100).toFixed(1)}%</span>
            </div>
          </div>

          {/* Document Headers */}
          <div className="mb-3 grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div className="bg-blue-50 p-3 rounded border-l-4 border-blue-400">
              <span className="font-medium text-blue-700">{rule1Name}:</span>
              <p className="text-gray-700 mt-1 text-xs">{comparison.rule1_section}</p>
            </div>
            <div className="bg-green-50 p-3 rounded border-l-4 border-green-400">
              <span className="font-medium text-green-700">{rule2Name}:</span>
              <p className="text-gray-700 mt-1 text-xs">{comparison.rule2_section}</p>
            </div>
          </div>

          {/* Comparison Content */}
          <div className="bg-gray-50 p-4 rounded border">
            <h4 className="font-medium text-gray-800 mb-3">Detailed Comparison</h4>
            <div 
              className="prose prose-sm max-w-none text-gray-700"
              dangerouslySetInnerHTML={{ 
                __html: comparison.comparison
                  .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                  .replace(/\*(.*?)\*/g, '<em>$1</em>')
                  .replace(/### (.*?)(\n|$)/g, '<h3 class="text-lg font-semibold mt-4 mb-2 text-gray-800">$1</h3>')
                  .replace(/\n\n/g, '</p><p class="mb-3">')
                  .replace(/^(.+)$/gm, '<p class="mb-3">$1</p>')
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default SectionComparison;