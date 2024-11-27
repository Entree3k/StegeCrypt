import logging
from pathlib import Path
from datetime import datetime

def cleanup_logs(log_dir: Path, max_logs: int = 2) -> None:
    """Clean up old log files."""
    try:
        log_files = []
        for log_file in log_dir.glob("stegecrypt_*.log"):
            try:
                creation_time = os.path.getctime(log_file)
                log_files.append((creation_time, log_file))
            except OSError:
                continue

        log_files.sort(reverse=True)
        for _, log_file in log_files[max_logs:]:
            try:
                log_file.unlink()
            except OSError:
                continue
    except Exception as e:
        logging.error(f"Error during log cleanup: {str(e)}")

def configure_logging(settings_manager):
    """Configure logging based on settings."""
    if not settings_manager.get("logging", "enabled"):
        logging.getLogger().setLevel(logging.CRITICAL)
        return

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    if settings_manager.get("logging", "file_logging"):
        cleanup_logs(log_dir, settings_manager.get("logging", "max_logs"))
    
    handlers = []
    log_level = getattr(logging, settings_manager.get("logging", "level").upper())
    
    if settings_manager.get("logging", "file_logging"):
        log_file = log_dir / f"stegecrypt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        handlers.append(logging.FileHandler(log_file))
    
    if settings_manager.get("logging", "console_logging"):
        handlers.append(logging.StreamHandler())
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )