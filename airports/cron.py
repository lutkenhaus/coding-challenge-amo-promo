import logging
import traceback
from django.core.management import call_command
from django.core.mail import mail_admins
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('LOGGING_FOR_CRON')

def import_airports_job():
    """
    Enhanced cron job function for importing airports with proper error handling
    """
    start_time = timezone.now()
    logger.info(f"=== Airport Import Cron Job Started at {start_time} ===")
    
    try:
        # Call the management command
        call_command('import_airports', '--force-update')
        
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        success_msg = f"Airport import completed successfully in {duration:.2f} seconds"
        logger.info(success_msg)
        
        return success_msg
        
    except Exception as e:
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        error_msg = f"Airport import failed after {duration:.2f} seconds: {str(e)}"
        error_traceback = traceback.format_exc()
        
        logger.error(f"{error_msg}\n{error_traceback}")
        
        # Send email notification if configured
        try:
            if hasattr(settings, 'ADMINS') and settings.ADMINS:
                mail_admins(
                    subject="Airport Import Cron Job Failed",
                    message=f"{error_msg}\n\nTraceback:\n{error_traceback}",
                    fail_silently=True
                )
        except Exception as mail_error:
            logger.error(f"Failed to send error notification email: {mail_error}")
        
        # Re-raise the exception so cron knows it failed
        raise e