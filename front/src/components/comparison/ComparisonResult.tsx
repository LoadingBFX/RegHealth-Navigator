import React, { useState } from 'react';
import { ComparisonResult as ComparisonResultType } from '../../services/api';
import SectionComparison from './SectionComparison';
import UniqueSection from './UniqueSection';
import ExecutiveSummary from './ExecutiveSummary';
import ComparisonStats from './ComparisonStats';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface Props {
  result: ComparisonResultType;
}

const ComparisonResult: React.FC<Props> = ({ result }) => {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    sections: true,
    unique: false,
    stats: false
  });

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Extract meaningful differences for display
  const getDocumentDisplayName = (rule: any) => {
    return `${rule.program} ${rule.year} ${rule.rule_type}`;
  };

  const shouldShowTopic = result.topic && result.topic !== 'general comparison' && result.topic !== 'fee schedule';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-200">
        {shouldShowTopic && (
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Comparison Topic: {result.topic}
          </h2>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white p-4 rounded-lg border-l-4 border-blue-400">
            <div className="flex items-center mb-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
              <span className="text-sm font-medium text-gray-600">Document A</span>
            </div>
            <p className="text-lg font-semibold text-blue-700">
              {getDocumentDisplayName(result.rule1)}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border-l-4 border-green-400">
            <div className="flex items-center mb-2">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
              <span className="text-sm font-medium text-gray-600">Document B</span>
            </div>
            <p className="text-lg font-semibold text-green-700">
              {getDocumentDisplayName(result.rule2)}
            </p>
          </div>
        </div>
      </div>

      {/* Executive Summary */}
      <ExecutiveSummary 
        summary={result.final_summary} 
        rule1={result.rule1}
        rule2={result.rule2}
      />

      {/* Section Comparisons */}
      <div className="bg-white border rounded-lg">
        <button
          onClick={() => toggleSection('sections')}
          className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50"
        >
          <h3 className="text-lg font-medium text-gray-800">
            Section-by-Section Comparisons ({result.section_comparisons.length})
          </h3>
          {expandedSections.sections ? (
            <ChevronUp className="h-5 w-5 text-gray-500" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-500" />
          )}
        </button>
        
        {expandedSections.sections && (
          <div className="px-6 pb-6 space-y-4">
            {result.section_comparisons.map((comparison, index) => (
              <SectionComparison 
                key={index} 
                comparison={comparison} 
                index={index + 1}
                rule1Name={getDocumentDisplayName(result.rule1)}
                rule2Name={getDocumentDisplayName(result.rule2)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Unique Sections */}
      {(result.rule1_unique_sections.sections.length > 0 || 
        result.rule2_unique_sections.sections.length > 0) && (
        <div className="bg-white border rounded-lg">
          <button
            onClick={() => toggleSection('unique')}
            className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50"
          >
            <h3 className="text-lg font-medium text-gray-800">
              Unique Sections
            </h3>
            {expandedSections.unique ? (
              <ChevronUp className="h-5 w-5 text-gray-500" />
            ) : (
              <ChevronDown className="h-5 w-5 text-gray-500" />
            )}
          </button>
          
          {expandedSections.unique && (
            <div className="px-6 pb-6 space-y-6">
              {result.rule1_unique_sections.sections.length > 0 && (
                <UniqueSection 
                  sections={result.rule1_unique_sections}
                  ruleLabel={getDocumentDisplayName(result.rule1)}
                  color="blue"
                />
              )}
              {result.rule2_unique_sections.sections.length > 0 && (
                <UniqueSection 
                  sections={result.rule2_unique_sections}
                  ruleLabel={getDocumentDisplayName(result.rule2)}
                  color="green"
                />
              )}
            </div>
          )}
        </div>
      )}

      {/* Statistics */}
      <div className="bg-white border rounded-lg">
        <button
          onClick={() => toggleSection('stats')}
          className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50"
        >
          <h3 className="text-lg font-medium text-gray-800">
            Comparison Statistics
          </h3>
          {expandedSections.stats ? (
            <ChevronUp className="h-5 w-5 text-gray-500" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-500" />
          )}
        </button>
        
        {expandedSections.stats && (
          <div className="px-6 pb-6">
            <ComparisonStats stats={result.stats} />
          </div>
        )}
      </div>
    </div>
  );
};

export default ComparisonResult;