def before_send(event, hint):
    '''
    Group like messages under the same fingerprint.
    '''
    from app import MISSING_PIN_ERROR, MISSING_DOCUMENT_ERROR, MISSING_IMAGE_ERROR

    event_message = event.get('message')

    if event_message:
        if event_message.startswith(MISSING_PIN_ERROR):
            event['fingerprint'] = ['no-image-for-pin']
        elif event_message.startswith(MISSING_DOCUMENT_ERROR):
            event['fingerprint'] = ['no-document-for-url']
        elif event_message.startswith(MISSING_IMAGE_ERROR):
            event['fingerprint'] = ['no-image-for-url']

    return event
