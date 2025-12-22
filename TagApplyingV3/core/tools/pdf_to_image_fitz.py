"""
Alternative PDF to Image Converter using PyMuPDF (fitz)

This module provides functionality to convert PDF files to images without requiring poppler.
Uses PyMuPDF (fitz) library which includes all necessary dependencies.
"""

import os
from pathlib import Path
from typing import List, Optional
import logging

try:
    import fitz  # PyMuPDF
    from PIL import Image
    import io
except ImportError as e:
    raise ImportError(f"Required packages not installed: {e}. Please install: pip install PyMuPDF pillow")

logger = logging.getLogger(__name__)


class PDFToImageConverterFitz:
    """Convert PDF files to images using PyMuPDF."""
    
    def __init__(self, output_dir: str = "pdf_outputs", dpi: int = 200):
        """
        Initialize the PDF to Image converter.
        
        Args:
            output_dir: Directory to save converted images
            dpi: Resolution for image conversion (dots per inch)
        """
        self.output_dir = output_dir
        self.dpi = dpi
        
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory set to: {self.output_dir}")
    
    def convert_pdf_to_images(
        self,
        pdf_path: str,
        image_format: str = "PNG",
        first_page: Optional[int] = None,
        last_page: Optional[int] = None,
        prefix: Optional[str] = None
    ) -> List[str]:
        """
        Convert a PDF file to images.
        
        Args:
            pdf_path: Path to the PDF file
            image_format: Image format (PNG, JPG, BMP, etc.)
            first_page: First page to convert (1-indexed, None = start from page 1)
            last_page: Last page to convert (1-indexed, None = convert all pages)
            prefix: Prefix for output image files
        
        Returns:
            List of paths to generated image files
        
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If page range is invalid
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        pdf_name = Path(pdf_path).stem
        prefix = prefix or pdf_name
        
        try:
            logger.info(f"Converting PDF: {pdf_path}")
            logger.info(f"DPI: {self.dpi}, Format: {image_format}")
            
            # Open PDF
            pdf_document = fitz.open(pdf_path)
            total_pages = len(pdf_document)
            
            # Set page range
            start_page = (first_page - 1) if first_page else 0
            end_page = min(last_page, total_pages) if last_page else total_pages
            
            output_paths = []
            
            # Render each page
            for page_num in range(start_page, end_page):
                logger.info(f"Rendering page {page_num + 1}...")
                
                try:
                    # Get page
                    page = pdf_document[page_num]
                    
                    # Calculate zoom factor based on DPI
                    # Standard DPI is 72, so zoom = dpi / 72
                    zoom = self.dpi / 72.0
                    mat = fitz.Matrix(zoom, zoom)
                    
                    # For very large PDFs, use clip to render in sections
                    try:
                        # Try normal rendering first
                        pix = page.get_pixmap(matrix=mat, alpha=False)
                    except MemoryError:
                        logger.warning(f"Page {page_num + 1} too large, rendering at lower resolution")
                        # Fall back to much lower zoom
                        mat = fitz.Matrix(0.25, 0.25)  # Quarter resolution
                        pix = page.get_pixmap(matrix=mat, alpha=False)
                    
                    # Convert to PIL Image
                    img_data = pix.tobytes("ppm")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Convert to RGB if necessary
                    if img.mode != 'RGB':
                        if image_format.upper() == "JPG":
                            img = img.convert('RGB')
                        # PNG can handle RGBA
                    
                    # Save image
                    output_filename = f"{prefix}_page_{page_num + 1}.{image_format.lower()}"
                    output_path = os.path.join(self.output_dir, output_filename)
                    
                    img.save(output_path, format=image_format.upper())
                    output_paths.append(output_path)
                    logger.info(f"Saved: {output_path}")
                    
                except Exception as page_error:
                    logger.warning(f"Error rendering page {page_num + 1}: {str(page_error)}")
                    continue
            
            pdf_document.close()
            logger.info(f"Successfully converted {len(output_paths)} pages")
            return output_paths
        
        except Exception as e:
            logger.error(f"Error converting PDF: {str(e)}")
            raise
    
    def convert_pdf_to_single_image(
        self,
        pdf_path: str,
        image_format: str = "PNG",
        output_filename: Optional[str] = None
    ) -> str:
        """
        Convert entire PDF to a single vertically stacked image.
        
        Args:
            pdf_path: Path to the PDF file
            image_format: Image format (PNG, JPG, BMP, etc.)
            output_filename: Custom output filename
        
        Returns:
            Path to the generated image file
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            logger.info(f"Converting PDF to single image: {pdf_path}")
            
            # Open PDF
            pdf_document = fitz.open(pdf_path)
            images = []
            
            # Render all pages
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                zoom = self.dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))
                
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                images.append(img)
            
            pdf_document.close()
            
            if not images:
                raise ValueError("No images generated from PDF")
            
            # Get dimensions
            width = images[0].width
            total_height = sum(img.height for img in images)
            
            # Create new image with combined height
            combined_image = Image.new('RGB', (width, total_height))
            
            # Paste all images vertically
            y_offset = 0
            for image in images:
                combined_image.paste(image, (0, y_offset))
                y_offset += image.height
            
            # Save combined image
            pdf_name = Path(pdf_path).stem
            output_filename = output_filename or f"{pdf_name}_combined.{image_format.lower()}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            combined_image.save(output_path, format=image_format.upper())
            logger.info(f"Saved combined image: {output_path}")
            
            return output_path
        
        except Exception as e:
            logger.error(f"Error converting PDF to single image: {str(e)}")
            raise
    
    def get_pdf_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            Number of pages in the PDF
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            pdf_document = fitz.open(pdf_path)
            page_count = len(pdf_document)
            pdf_document.close()
            logger.info(f"PDF has {page_count} pages")
            return page_count
        except Exception as e:
            logger.error(f"Error reading PDF: {str(e)}")
            raise


# Convenience functions
def pdf_to_images(
    pdf_path: str,
    output_dir: str = "pdf_outputs",
    dpi: int = 200,
    image_format: str = "PNG"
) -> List[str]:
    """
    Quick function to convert PDF to images.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save images
        dpi: Resolution for conversion
        image_format: Output image format
    
    Returns:
        List of output image paths
    """
    converter = PDFToImageConverterFitz(output_dir=output_dir, dpi=dpi)
    return converter.convert_pdf_to_images(pdf_path, image_format=image_format)


def pdf_to_single_image(
    pdf_path: str,
    output_dir: str = "pdf_outputs",
    dpi: int = 200,
    image_format: str = "PNG"
) -> str:
    """
    Quick function to convert entire PDF to a single image.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save image
        dpi: Resolution for conversion
        image_format: Output image format
    
    Returns:
        Path to the output image
    """
    converter = PDFToImageConverterFitz(output_dir=output_dir, dpi=dpi)
    return converter.convert_pdf_to_single_image(pdf_path, image_format=image_format)
