import React, { useEffect, useRef } from 'react';
import { useStore } from '../../store/store';
import { RefreshCw } from 'lucide-react';

// This is a simplified version. In a real implementation, 
// we would use markmap-view to render the actual mind map.
const MindmapTab: React.FC = () => {
  const { mindmap, setProcessing, setProcessingProgress } = useStore();
  const svgRef = useRef<SVGSVGElement>(null);
  
  const handleGenerateMindmap = () => {
    // Simulate processing
    setProcessing(true);
    let progress = 0;
    
    const interval = setInterval(() => {
      progress += 5;
      setProcessingProgress(progress);
      
      if (progress >= 100) {
        clearInterval(interval);
        setProcessing(false);
        setProcessingProgress(0);
      }
    }, 300);
  };
  
  // In a real implementation, this would use markmap-view to render
  // the mind map from the data structure
  useEffect(() => {
    if (!mindmap || !svgRef.current) return;
    
    // This is placeholder code - in a real implementation we would use
    // the markmap library to render an actual interactive mind map
    const svg = svgRef.current;
    svg.innerHTML = '';
    
    // Simple visual representation (not a real mind map)
    const width = svg.clientWidth;
    const height = svg.clientHeight;
    
    // Create central node
    const centralNode = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    centralNode.setAttribute('cx', (width / 2).toString());
    centralNode.setAttribute('cy', (height / 2).toString());
    centralNode.setAttribute('r', '30');
    centralNode.setAttribute('fill', '#1A365D');
    svg.appendChild(centralNode);
    
    // Create central text
    const centralText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    centralText.setAttribute('x', (width / 2).toString());
    centralText.setAttribute('y', (height / 2).toString());
    centralText.setAttribute('text-anchor', 'middle');
    centralText.setAttribute('dominant-baseline', 'middle');
    centralText.setAttribute('fill', 'white');
    centralText.setAttribute('font-size', '12');
    centralText.textContent = 'FDA Guidance';
    svg.appendChild(centralText);
    
    // Create branches (simplified)
    mindmap.children.forEach((child, index) => {
      const angle = (index * 2 * Math.PI) / mindmap.children.length;
      const x1 = width / 2;
      const y1 = height / 2;
      const x2 = x1 + Math.cos(angle) * 100;
      const y2 = y1 + Math.sin(angle) * 100;
      
      // Draw line
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', x1.toString());
      line.setAttribute('y1', y1.toString());
      line.setAttribute('x2', x2.toString());
      line.setAttribute('y2', y2.toString());
      line.setAttribute('stroke', '#4299E1');
      line.setAttribute('stroke-width', '2');
      svg.appendChild(line);
      
      // Draw node
      const node = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      node.setAttribute('cx', x2.toString());
      node.setAttribute('cy', y2.toString());
      node.setAttribute('r', '20');
      node.setAttribute('fill', '#4299E1');
      svg.appendChild(node);
      
      // Add text
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', x2.toString());
      text.setAttribute('y', y2.toString());
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('dominant-baseline', 'middle');
      text.setAttribute('fill', 'white');
      text.setAttribute('font-size', '10');
      text.textContent = child.name.split(' ')[0];
      svg.appendChild(text);
    });
    
  }, [mindmap]);

  return (
    <div className="p-4 h-full flex flex-col">
      {mindmap ? (
        <>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-neutral-800">{mindmap.title} - Mind Map</h2>
            <div className="flex space-x-1">
              <button 
                className="p-1.5 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
                title="Regenerate mind map"
                onClick={handleGenerateMindmap}
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>
          </div>
          
          <div className="flex-1 border border-neutral-200 rounded-md bg-white p-2 overflow-hidden">
            <div className="bg-white h-full w-full overflow-auto">
              <svg 
                ref={svgRef} 
                width="100%" 
                height="100%" 
                viewBox="0 0 800 600" 
                className="mindmap-svg"
              ></svg>
              
              <div className="text-xs text-neutral-500 mt-2 text-center">
                <p>Click on nodes to expand/collapse branches. Drag to reposition the mind map.</p>
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center justify-center h-full text-center p-6">
          <div className="bg-primary-50 p-4 rounded-full mb-4">
            <GitBranch className="h-8 w-8 text-primary-700" />
          </div>
          <h3 className="text-lg font-medium text-neutral-800 mb-2">Generate a Mind Map</h3>
          <p className="text-neutral-500 mb-6">
            Create an interactive visualization of the document structure with clickable nodes linked to source content.
          </p>
          <button 
            className="px-4 py-2 bg-primary-700 hover:bg-primary-800 text-white rounded-md transition-colors flex items-center"
            onClick={handleGenerateMindmap}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Generate Mind Map
          </button>
        </div>
      )}
    </div>
  );
};

// Importing icon to use in component
import { GitBranch } from 'lucide-react';

export default MindmapTab;