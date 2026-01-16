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
    # Make standard fields optional in form validation, enforcing logic in clean()
    source_path = forms.CharField(
        max_length=1024, required=False, label="Source Path (Device)"
    )
    destination_path = forms.CharField(
        max_length=1024, required=False, label="Destination Path (Image)"
    )
    source_upload = forms.FileField(required=False, label="Upload Evidence File")

    # Physical Device Selection
    physical_device = forms.ChoiceField(
        required=False, label="Select Physical Device", choices=[]
    )

    class Meta:
        model = AcquisitionTask
        fields = [
            "type",
            "source_path",
            "physical_device",
            "source_upload",
            "destination_path",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .utils import PhysicalDiscoveryService

        devices = PhysicalDiscoveryService.list_devices()
        choices = [("", "--- Select a Device ---")]
        for dev in devices:
            choices.append(
                (
                    dev["path"],
                    f"{dev['model']} ({dev['size']}) - {dev['path']} {'[MOUNTED]' if dev['is_mounted'] else ''}",
                )
            )
        self.fields["physical_device"].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        type_ = cleaned_data.get("type")
        physical_device = cleaned_data.get("physical_device")

        if type_ == "file_upload":
            if not cleaned_data.get("source_upload"):
                self.add_error("source_upload", "Please upload a file.")
        elif type_ in ["disk_physical", "disk_expert"]:
            # If a physical device was selected from the dropdown, use it as source_path
            if physical_device:
                cleaned_data["source_path"] = physical_device

            if not cleaned_data.get("source_path"):
                self.add_error(
                    "source_path",
                    "Please select a physical device or provide a source path.",
                )
            if not cleaned_data.get("destination_path"):
                # Default destination for physical images if not provided
                if cleaned_data.get("evidence_name"):
                    cleaned_data["destination_path"] = (
                        f"/tmp/{cleaned_data['evidence_name']}.img"
                    )
                else:
                    self.add_error("destination_path", "Destination path is required.")

        return cleaned_data

    def save(self, commit=True, user=None):
        # 1. Create Evidence
        evidence = Evidence.objects.create(
            case=self.cleaned_data["case"],
            name=self.cleaned_data["evidence_name"],
            source_type=self.cleaned_data["source_type"],
            size_bytes=0,
            acquired_by=user,
        )

        # 2. Create Task
        task = super().save(commit=False)
        task.evidence = evidence
        task.created_by = user
        # Ensure source_path is set from clean data (which might have come from physical_device)
        task.source_path = self.cleaned_data.get("source_path")
        if commit:
            task.save()
        return task
