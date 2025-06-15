import unittest
from datetime import datetime
from core.data_fetcher.federal_register.models import DocumentType, Agency, Document
from core.data_fetcher.federal_register.client import FederalRegisterClient

class TestFederalRegisterAPI(unittest.TestCase):
    """Test cases for Federal Register API integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = FederalRegisterClient(download_delay=0)  # No delay for tests
        
        # Sample API response based on actual data
        self.sample_response = {
            "count": 2,
            "description": "Documents published from 05/29/2025 to 06/05/2025",
            "total_pages": 1,
            "results": [
                {
                    "title": "Medicare Program; Hospital Inpatient Prospective Payment Systems",
                    "type": "Proposed Rule",
                    "abstract": "This document corrects technical and typographical errors...",
                    "document_number": "2025-10261",
                    "html_url": "https://www.federalregister.gov/documents/2025/06/05/2025-10261/...",
                    "pdf_url": "https://www.govinfo.gov/content/pkg/FR-2025-06-05/pdf/2025-10261.pdf",
                    "publication_date": "2025-06-05",
                    "agencies": [
                        {
                            "raw_name": "DEPARTMENT OF HEALTH AND HUMAN SERVICES",
                            "name": "Health and Human Services Department",
                            "id": 221,
                            "url": "https://www.federalregister.gov/agencies/health-and-human-services-department",
                            "json_url": "https://www.federalregister.gov/api/v1/agencies/221",
                            "parent_id": None,
                            "slug": "health-and-human-services-department"
                        },
                        {
                            "raw_name": "Centers for Medicare & Medicaid Services",
                            "name": "Centers for Medicare & Medicaid Services",
                            "id": 45,
                            "url": "https://www.federalregister.gov/agencies/centers-for-medicare-medicaid-services",
                            "json_url": "https://www.federalregister.gov/api/v1/agencies/45",
                            "parent_id": 221,
                            "slug": "centers-for-medicare-medicaid-services"
                        }
                    ]
                }
            ]
        }
    
    def test_document_type_parsing(self):
        """Test parsing of document types from API response."""
        # Test valid document types
        self.assertEqual(DocumentType.from_api_type("Rule"), DocumentType.RULE)
        self.assertEqual(DocumentType.from_api_type("Proposed Rule"), DocumentType.PROPOSED_RULE)
        
        # Test invalid document type
        with self.assertRaises(ValueError):
            DocumentType.from_api_type("Invalid Type")
    
    def test_document_parsing(self):
        """Test parsing of document data from API response."""
        doc_data = self.sample_response["results"][0]
        doc = self.client._parse_document(doc_data)
        
        # Verify document attributes
        self.assertEqual(doc.title, doc_data["title"])
        self.assertEqual(doc.document_number, doc_data["document_number"])
        self.assertEqual(doc.type, DocumentType.PROPOSED_RULE)
        self.assertEqual(doc.publication_date, datetime.strptime(doc_data["publication_date"], "%Y-%m-%d"))
        self.assertEqual(doc.html_url, doc_data["html_url"])
        
        # Verify agencies
        self.assertEqual(len(doc.agencies), 2)
        self.assertEqual(doc.agencies[0].name, "Health and Human Services Department")
        self.assertEqual(doc.agencies[1].name, "Centers for Medicare & Medicaid Services")
    
    def test_document_filename_generation(self):
        """Test generation of document filenames."""
        doc_data = self.sample_response["results"][0]
        doc = self.client._parse_document(doc_data)
        
        # Test without program type
        with self.assertRaises(ValueError):
            _ = doc.filename
        
        # Test with program type
        doc.program_type = "MPFS"
        self.assertEqual(doc.filename, "2025_MPFS_proposed.xml")
    
    def test_document_type_checks(self):
        """Test document type checking methods."""
        # Test proposed rule
        doc_data = self.sample_response["results"][0]
        doc = self.client._parse_document(doc_data)
        self.assertTrue(doc.is_proposed)
        self.assertFalse(doc.is_final)
        
        # Test final rule
        doc_data["type"] = "Rule"
        doc = self.client._parse_document(doc_data)
        self.assertTrue(doc.is_final)
        self.assertFalse(doc.is_proposed)

if __name__ == '__main__':
    unittest.main() 