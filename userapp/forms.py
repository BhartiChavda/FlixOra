from django import forms
from django.contrib.auth.models import User
from .models import Movie, Review, Comment, Profile, Watchlist, Rating

class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ['title', 'description', 'poster', 'poster_url', 'genre', 'media_type', 'language', 'release_date', 'trailer_url', 'cast_info']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter Movie Title'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Write movie description...'}),
            'poster_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://example.com/poster.jpg'}),
            'genre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Action, Comedy, Sci-Fi'}),
            'media_type': forms.Select(attrs={'class': 'form-input'}),
            'language': forms.Select(attrs={'class': 'form-input'}),
            'release_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'trailer_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'e.g. https://www.youtube.com/embed/dQw4w9WgXcQ'}),
            'cast_info': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Director: X | Stars: Y, Z'}),
        }

class RatingForm(forms.ModelForm):
    story_rating = forms.IntegerField(
        min_value=1, max_value=10,
        widget=forms.NumberInput(attrs={'class': 'bg-[#15151e] border border-brand-purple/20 rounded-xl px-4 py-2 text-white w-24 text-center focus:outline-none', 'min': '1', 'max': '10'})
    )
    acting_rating = forms.IntegerField(
        min_value=1, max_value=10,
        widget=forms.NumberInput(attrs={'class': 'bg-[#15151e] border border-brand-purple/20 rounded-xl px-4 py-2 text-white w-24 text-center focus:outline-none', 'min': '1', 'max': '10'})
    )
    music_rating = forms.IntegerField(
        min_value=1, max_value=10,
        widget=forms.NumberInput(attrs={'class': 'bg-[#15151e] border border-brand-purple/20 rounded-xl px-4 py-2 text-white w-24 text-center focus:outline-none', 'min': '1', 'max': '10'})
    )
    visual_rating = forms.IntegerField(
        min_value=1, max_value=10,
        widget=forms.NumberInput(attrs={'class': 'bg-[#15151e] border border-brand-purple/20 rounded-xl px-4 py-2 text-white w-24 text-center focus:outline-none', 'min': '1', 'max': '10'})
    )

    class Meta:
        model = Rating
        fields = ['story_rating', 'acting_rating', 'music_rating', 'visual_rating']

class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        min_value=1, max_value=10,
        widget=forms.NumberInput(attrs={'class': 'bg-[#15151e] border border-brand-purple/20 rounded-xl px-4 py-2 text-white w-24 text-center focus:outline-none', 'min': '1', 'max': '10'})
    )
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'w-full bg-[#15151e] border border-brand-purple/20 rounded-2xl p-4 text-white focus:outline-none focus:border-brand-purple/65 transition-all resize-none',
                'rows': 3,
                'placeholder': 'Share your detailed review vibe on this movie...'
            }),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'bg-[#15151e] border border-brand-purple/20 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-brand-purple/65 transition-all w-full',
                'placeholder': 'Reply to this review bubble...'
            })
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-input w-full bg-[#15151e] border border-brand-purple/20 rounded-2xl p-4 text-white focus:outline-none',
                'rows': 3,
                'placeholder': 'Tell other critics about your taste in cinema...'
            }),
        }

class WatchlistForm(forms.ModelForm):
    class Meta:
        model = Watchlist
        fields = ['status', 'is_public']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'bg-[#15151e] border border-brand-purple/20 rounded-xl px-4 py-2 text-white focus:outline-none'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'rounded border-brand-purple/20 bg-[#15151e] focus:ring-0 focus:ring-offset-0 text-brand-purple'
            })
        }

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Password'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm Password'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email Address'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            self.fields['username'].help_text = ''

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match.")
        return cleaned_data
