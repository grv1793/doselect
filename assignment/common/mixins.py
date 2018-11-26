"""Use these mixins for Creation, Updateion, Deletion of model instances."""


class UpdateModelMixin(object):
    """Update a model instance."""

    def update(self, data, instance, serializer_class, **kwargs):
        """Update a model instance."""
        if not data:
            return None
        partial = kwargs.pop('partial', False)
        context = kwargs.pop('context') if kwargs.get('context', None) else None
        serializer = serializer_class(instance, data=data, partial=partial, context=context)
        serializer.is_valid(raise_exception=True)

        return self.perform_update(serializer)

    def perform_update(self, serializer):
        """Action to be performed here."""
        return serializer.save()

    def partial_update(self, request, *args, **kwargs):
        """Partial Updation of fields of a model instance."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class CreateModelMixin(object):
    """Create a model instance."""

    def create(self, data, serializer_class, **kwargs):
        """Create a model instance."""
        context = kwargs.pop('context', None)
        serializer = serializer_class(data=data, context=context)
        serializer.is_valid(raise_exception=True)

        return self.perform_create(serializer)

    def perform_create(self, serializer):
        """Action to be performed here."""
        return serializer.save()


class DestroyModelMixin(object):
    """Destroy a model instance."""

    def destroy(self, instance, *args, **kwargs):
        """Destroy a model instance."""
        self.perform_destroy(instance)

    def perform_destroy(self, instance):
        """Action to be performed here."""
        instance.delete()
