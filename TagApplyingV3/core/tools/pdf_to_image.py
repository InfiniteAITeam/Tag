"""
PDF to Image Converter Module

This module provides functionality to convert PDF files to images (PNG, JPG, etc.)
using PyPDF2 for PDF handling and Pillow for image processing.
"""

import os
from pathlib import Path
from typing import List, Optional
import logging

try:
    from pdf2image import convert_from_path, convert_from_bytes
    from PIL import Image
    import PyPDF2
except ImportError as e:
    raise ImportError(f"Required packages not installed: {e}. Please install: pip install pdf2image pillow PyPDF2 poppler-utils")

logger = logging.getLogger(__name__)


class PDFToImageConverter:
    """Convert PDF files to images."""
    
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
            
            # Convert PDF pages to images
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                first_page=first_page,
                last_page=last_page
            )
            
            if not images:
                raise ValueError("No images generated from PDF")
            
            output_paths = []
            for idx, image in enumerate(images, start=1):
                page_num = first_page + idx - 1 if first_page else idx
                output_filename = f"{prefix}_page_{page_num}.{image_format.lower()}"
                output_path = os.path.join(self.output_dir, output_filename)
                
                image.save(output_path, format=image_format)
                output_paths.append(output_path)
                logger.info(f"Saved: {output_path}")
            
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
            
            # Convert all pages
            images = convert_from_path(pdf_path, dpi=self.dpi)
            
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
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                combined_image.paste(image, (0, y_offset))
                y_offset += image.height
            
            # Save combined image
            pdf_name = Path(pdf_path).stem
            output_filename = output_filename or f"{pdf_name}_combined.{image_format.lower()}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            combined_image.save(output_path, format=image_format)
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
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
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
    converter = PDFToImageConverter(output_dir=output_dir, dpi=dpi)
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
    converter = PDFToImageConverter(output_dir=output_dir, dpi=dpi)
    return converter.convert_pdf_to_single_image(pdf_path, image_format=image_format)
