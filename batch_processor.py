"""Batch-Verarbeitung mit OPTIMIERTEM Multiprocessing"""
import concurrent.futures
from pathlib import Path
from typing import List, Tuple, Callable
import multiprocessing as mp

class BatchProcessor:
    """Verarbeitet mehrere Dateien parallel mit Multiprocessing (nicht Threading!)"""
    
    def __init__(self, max_workers: int = None):
        # PERFORMANCE: Auto-detect optimal worker count
        if max_workers is None:
            max_workers = min(mp.cpu_count(), 4)  # Max 4 für I/O-bound tasks
        self.max_workers = max_workers
        self.results = []
    
    def process_files(
        self, 
        files: List[str], 
        process_func: Callable,
        progress_callback: Callable = None
    ) -> List[Tuple[str, any, bool]]:
        """
        Verarbeitet Dateien parallel mit ProcessPoolExecutor (GIL-frei!)
        
        PERFORMANCE: Nutzt Multiprocessing statt Threading für CPU-bound tasks
        """
        results = []
        total = len(files)
        
        # PERFORMANCE: ProcessPoolExecutor für echte Parallelität
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Starte alle Tasks
            future_to_file = {
                executor.submit(self._safe_process, process_func, file): file 
                for file in files
            }
            
            # Sammle Ergebnisse
            for i, future in enumerate(concurrent.futures.as_completed(future_to_file)):
                file = future_to_file[future]
                
                try:
                    result, success = future.result()
                    results.append((file, result, success))
                    
                    if progress_callback:
                        progress_callback(i + 1, total, f"Verarbeitet: {Path(file).name}")
                        
                except Exception as e:
                    results.append((file, str(e), False))
                    if progress_callback:
                        progress_callback(i + 1, total, f"Fehler: {Path(file).name}")
        
        return results
    
    @staticmethod
    def _safe_process(func: Callable, file: str) -> Tuple[any, bool]:
        """Führt Verarbeitung mit Fehlerbehandlung aus"""
        try:
            result = func(file)
            return result, True
        except Exception as e:
            return str(e), False
    
    def estimate_total_time(self, file_count: int, avg_time_per_file: float) -> dict:
        """Schätzt Gesamtzeit für Batch-Verarbeitung"""
        sequential_time = file_count * avg_time_per_file
        parallel_time = sequential_time / self.max_workers
        
        return {
            'sequential_seconds': sequential_time,
            'parallel_seconds': parallel_time,
            'speedup': f"{self.max_workers}x schneller",
            'workers': self.max_workers
        }
