from app.features.localization.service import LocalizationService


_localization_service = None


def get_localization_service() -> LocalizationService:
    global _localization_service
    if _localization_service is None:
        _localization_service = LocalizationService()
    return _localization_service