import config from '../config';

export interface ComparisonRule {
  program: string;
  year: number;
  rule_type: string;
  topic: string;
  source_file?: string;
  pdf_url?: string;
  html_url?: string;
  document_title?: string;
}

export interface SectionComparison {
  rule1_section: string;
  rule2_section: string;
  similarity_score: number;
  comparison: string;
  chunk_counts: {
    rule1: number;
    rule2: number;
  };
  token_usage: {
    rule1_context: number;
    rule2_context: number;
  };
}

export interface UniqueSection {
  section_name: string;
  chunk_count: number;
  summary: string;
}

export interface UniqueSectionAnalysis {
  sections: UniqueSection[];
  analysis: string;
}

export interface ComparisonStats {
  total_sections_compared: number;
  rule1_unique_sections: number;
  rule2_unique_sections: number;
  rule1_total_chunks: number;
  rule2_total_chunks: number;
}

export interface ComparisonResult {
  rule1: ComparisonRule;
  rule2: ComparisonRule;
  topic: string;
  section_comparisons: SectionComparison[];
  rule1_unique_sections: UniqueSectionAnalysis;
  rule2_unique_sections: UniqueSectionAnalysis;
  final_summary: string;
  stats: ComparisonStats;
}

export interface CompareApiRequest {
  message: string;
}

export interface ApiError {
  error: string;
}

export interface DocumentInfo {
  pdf_url: string;
  html_url: string;
  title: string;
  publication_date: string;
  document_number: string;
}

export class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = config.api.baseUrl;
  }

  private extractDocumentNumber(documentName: string): string | null {
    // Extract document number from names like "2024_MPFS_final_2024-14828"
    const match = documentName.match(/(\d{4}-\d{5})$/);
    return match ? match[1] : null;
  }

  async compareRules(query: string): Promise<ComparisonResult> {
    try {
      const response = await fetch(`${this.baseUrl}${config.api.endpoints.compare}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: query } as CompareApiRequest),
      });

      if (!response.ok) {
        const errorData: ApiError = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const result: ComparisonResult = await response.json();
      return result;
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Failed to compare rules: ${error.message}`);
      }
      throw new Error('Failed to compare rules: Unknown error occurred');
    }
  }

  async chatWithDocuments(query: string, docNames: string[] = []): Promise<{
    response: string;
    sources: Array<{
      name: string;
      chunks: Array<{
        text: string;
        index: number;
        distance: number;
      }>;
    }>;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}${config.api.endpoints.chat}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query, 
          doc_names: docNames 
        }),
      });

      if (!response.ok) {
        const errorData: ApiError = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Failed to chat with documents: ${error.message}`);
      }
      throw new Error('Failed to chat with documents: Unknown error occurred');
    }
  }

  async getDocumentInfo(documentName: string): Promise<DocumentInfo | null> {
    try {
      const docNumber = this.extractDocumentNumber(documentName);
      if (!docNumber) {
        return null;
      }

      const response = await fetch(`${this.baseUrl}${config.api.endpoints.federalRegister}/${docNumber}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          return null; // Document not found, but not an error
        }
        const errorData: ApiError = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const result: DocumentInfo = await response.json();
      return result;
    } catch (error) {
      console.warn(`Failed to get document info for ${documentName}:`, error);
      return null; // Return null instead of throwing to avoid breaking the UI
    }
  }
}

export const apiService = new ApiService();