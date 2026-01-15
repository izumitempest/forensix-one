from django import forms
from .models import AcquisitionTask
from apps.cases.models import Case, Evidence


class AcquisitionForm(forms.ModelForm):
    # Extra fields for Evidence creation
    case = forms.ModelChoiceField(queryset=Case.objects.all(), label="Assign to Case")
    evidence_name = forms.CharField(max_length=255, label="Evidence Label")
    source_type = forms.ChoiceField(
        choices=[
            ("disk", "Disk"),
            ("memory", "Memory"),
            ("mobile", "Mobile"),
            ("cloud", "Cloud"),
        ]
    )

    class Meta:
        model = AcquisitionTask
        fields = ["type", "source_path", "destination_path"]

    def save(self, commit=True, user=None):
        # 1. Create Evidence
        evidence = Evidence.objects.create(
            case=self.cleaned_data["case"],
            name=self.cleaned_data["evidence_name"],
            source_type=self.cleaned_data["source_type"],
            acquired_by=user,
        )

        # 2. Create Task
        task = super().save(commit=False)
        task.evidence = evidence
        task.created_by = user
        if commit:
            task.save()
        return task
