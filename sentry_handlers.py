def before_send(event, hint):
    '''
    Group like messages under the same fingerprint.
    '''
    event_message = event.get('message')

    if event_message:
        if event_message.startswith('Could not find image for PIN'):
            event['fingerprint'] = ['no-image-for-pin']
        elif event_message.startswith('Could not find document at URL'):
            event['fingerprint'] = ['no-document-for-url']
        elif event_message.startswith('Image does not exist at'):
            event['fingerprint'] = ['no-image-for-url']

    return event
