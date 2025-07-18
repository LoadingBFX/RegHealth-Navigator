import React from 'react';
import { FileText, Star, TrendingUp, ExternalLink, AlertTriangle } from 'lucide-react';

interface Props {
  summary: string;
  rule1?: any;
  rule2?: any;
}

const ExecutiveSummary: React.FC<Props> = ({ summary, rule1, rule2 }) => {
  const formatSummary = (text: string) => {
    return text
      // Convert markdown headers
      .replace(/#### (.*?)(\n|$)/g, '<h4 class="text-lg font-semibold mt-6 mb-3 text-gray-800 flex items-center"><span class="bg-blue-100 text-blue-800 p-1 rounded mr-2 text-sm">$1</span></h4>')
      .replace(/### (.*?)(\n|$)/g, '<h3 class="text-xl font-semibold mt-6 mb-4 text-gray-800 border-b border-gray-200 pb-2">$1</h3>')
      // Convert bold text
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-800">$1</strong>')
      // Convert italic text
      .replace(/\*(.*?)\*/g, '<em class="italic text-gray-700">$1</em>')
      // Convert bullet points
      .replace(/^- (.*?)$/gm, '<li class="ml-4 mb-2 text-gray-700">• $1</li>')
      // Convert numbered lists
      .replace(/^\d+\. (.*?)$/gm, '<li class="ml-4 mb-2 text-gray-700 list-decimal">$1</li>')
      // Convert paragraphs
      .replace(/\n\n/g, '</p><p class="mb-4 text-gray-700 leading-relaxed">')
      .replace(/^(.+)$/gm, '<p class="mb-4 text-gray-700 leading-relaxed">$1</p>');
  };

  return (
    <div className="bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 border-2 border-amber-300 rounded-xl p-6 shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <div className="bg-gradient-to-br from-amber-100 to-yellow-100 p-3 rounded-xl mr-4 shadow-sm">
            <Star className="h-6 w-6 text-amber-600" />
          </div>
          <div>
            <h3 className="text-2xl font-bold text-gray-800">
              Executive Summary
            </h3>
            <p className="text-sm text-amber-700 mt-1">Key findings and insights</p>
          </div>
        </div>
        <div className="bg-amber-100 p-2 rounded-lg">
          <TrendingUp className="h-5 w-5 text-amber-600" />
        </div>
      </div>
      
      <div className="bg-white rounded-xl p-6 border border-amber-200 shadow-sm">
        <div 
          className="prose prose-lg max-w-none text-gray-800"
          dangerouslySetInnerHTML={{ 
            __html: formatSummary(summary)
          }}
        />
      </div>
      
      <div className="mt-6 space-y-3">
        {/* Warning */}
        <div className="flex items-start space-x-3 text-sm text-orange-800 bg-gradient-to-r from-orange-50 to-yellow-50 p-4 rounded-lg border border-orange-200">
          <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium mb-1">Important Notice:</p>
            <p className="text-xs leading-relaxed">
              RegHealth-Navigator can make mistakes. Please double-check responses and verify important information with official sources.
            </p>
          </div>
        </div>

        {/* Source Links */}
        <div className="flex items-start space-x-3 text-sm text-blue-800 bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
          <ExternalLink className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <div className="w-full">
            <p className="font-medium mb-2">View Original Documents:</p>
            <div className="space-y-2 text-xs">
              {rule1?.pdf_url && rule1?.html_url ? (
                <div className="bg-white p-3 rounded-lg border border-blue-100">
                  <div className="font-medium text-blue-800 mb-2">
                    {rule1.program} {rule1.year} {rule1.rule_type}
                  </div>
                  <div className="space-y-1">
                    <a 
                      href={rule1.html_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center space-x-2 text-blue-700 hover:text-blue-900 hover:underline"
                    >
                      <FileText className="h-3 w-3" />
                      <span>View HTML Version</span>
                    </a>
                    <a 
                      href={rule1.pdf_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center space-x-2 text-blue-700 hover:text-blue-900 hover:underline"
                    >
                      <FileText className="h-3 w-3" />
                      <span>Download PDF</span>
                    </a>
                  </div>
                </div>
              ) : rule1 && (
                <a 
                  href={`https://www.federalregister.gov/documents/search?conditions%5Bterm%5D=${encodeURIComponent(`${rule1.program} ${rule1.year} ${rule1.rule_type}`)}`}
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2 text-blue-700 hover:text-blue-900 hover:underline"
                >
                  <ExternalLink className="h-3 w-3" />
                  <span>{rule1.program} {rule1.year} {rule1.rule_type} - Federal Register</span>
                </a>
              )}
              {rule2?.pdf_url && rule2?.html_url ? (
                <div className="bg-white p-3 rounded-lg border border-blue-100">
                  <div className="font-medium text-blue-800 mb-2">
                    {rule2.program} {rule2.year} {rule2.rule_type}
                  </div>
                  <div className="space-y-1">
                    <a 
                      href={rule2.html_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center space-x-2 text-blue-700 hover:text-blue-900 hover:underline"
                    >
                      <FileText className="h-3 w-3" />
                      <span>View HTML Version</span>
                    </a>
                    <a 
                      href={rule2.pdf_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center space-x-2 text-blue-700 hover:text-blue-900 hover:underline"
                    >
                      <FileText className="h-3 w-3" />
                      <span>Download PDF</span>
                    </a>
                  </div>
                </div>
              ) : rule2 && (
                <a 
                  href={`https://www.federalregister.gov/documents/search?conditions%5Bterm%5D=${encodeURIComponent(`${rule2.program} ${rule2.year} ${rule2.rule_type}`)}`}
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2 text-blue-700 hover:text-blue-900 hover:underline"
                >
                  <ExternalLink className="h-3 w-3" />
                  <span>{rule2.program} {rule2.year} {rule2.rule_type} - Federal Register</span>
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExecutiveSummary;