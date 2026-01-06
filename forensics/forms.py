from django import forms
from .models import Document

class DocumentForm(forms.ModelForm):
    """Form for uploading documents to a case"""
    class Meta:
        model = Document
        fields = ['document_type', 'title', 'description', 'file_path', 'evidence', 'author', 'access_level', 'is_confidential']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'title': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'placeholder': 'Document title'}),
            'description': forms.Textarea(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'rows': 3, 'placeholder': 'Optional description'}),
            'file_path': forms.FileInput(attrs={'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'}),
            'evidence': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'author': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'placeholder': 'Author name'}),
            'access_level': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'is_confidential': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
        }
        labels = {
            'document_type': 'Document Type',
            'title': 'Title',
            'description': 'Description',
            'file_path': 'File',
            'evidence': 'Related Evidence (Optional)',
            'author': 'Author',
            'access_level': 'Access Level',
            'is_confidential': 'Mark as Confidential',
        }
    
    def __init__(self, *args, **kwargs):
        case = kwargs.pop('case', None)
        super().__init__(*args, **kwargs)
        
        # Make evidence field optional and filter by case
        self.fields['evidence'].required = False
        if case:
            self.fields['evidence'].queryset = case.evidence.all()
            self.fields['evidence'].empty_label = "None (Case document only)"
