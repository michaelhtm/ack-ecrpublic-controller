	err = rm.syncTags(ctx, desired, &resource{ko})
	if err != nil {
		return nil, err
	}