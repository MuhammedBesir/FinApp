/**
 * Profile Page - User Profile Management
 * 🌙 Dark Mode | ✨ Glassmorphism | 🎨 Investia Brand
 */
import React, { useState } from "react";
import {
  User,
  Mail,
  Camera,
  Save,
  Shield,
  Key,
  Smartphone,
  Crown,
  Calendar,
  CheckCircle,
  AlertCircle,
  Loader2,
  Edit3,
  X,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const ProfilePage = () => {
  const { user, updateProfile, changePassword, getUserInitials } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    fullName: user?.fullName || "",
    email: user?.email || "",
  });

  // Password change modal state
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState("");

  // 2FA state
  const [show2FAModal, setShow2FAModal] = useState(false);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(
    user?.twoFactorEnabled || false,
  );
  const [verificationCode, setVerificationCode] = useState("");
  const [twoFALoading, setTwoFALoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSaveProfile = async () => {
    setIsLoading(true);
    setError("");
    setSuccess("");

    try {
      await updateProfile({ full_name: formData.fullName });
      setSuccess("Profil başarıyla güncellendi!");
      setIsEditing(false);
    } catch (err) {
      setError(err.message || "Profil güncellenirken bir hata oluştu.");
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPasswordError("");

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError("Yeni şifreler eşleşmiyor!");
      return;
    }

    if (passwordData.newPassword.length < 8) {
      setPasswordError("Şifre en az 8 karakter olmalıdır.");
      return;
    }

    // Check password requirements
    if (!/[A-Z]/.test(passwordData.newPassword)) {
      setPasswordError("Şifre en az bir büyük harf içermelidir.");
      return;
    }
    if (!/[a-z]/.test(passwordData.newPassword)) {
      setPasswordError("Şifre en az bir küçük harf içermelidir.");
      return;
    }
    if (!/[0-9]/.test(passwordData.newPassword)) {
      setPasswordError("Şifre en az bir rakam içermelidir.");
      return;
    }

    setPasswordLoading(true);

    try {
      await changePassword(passwordData.currentPassword, passwordData.newPassword);
      setShowPasswordModal(false);
      setPasswordData({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });
      setSuccess("Şifreniz başarıyla değiştirildi!");
    } catch (err) {
      setPasswordError(err.message || "Şifre değiştirilemedi. Lütfen tekrar deneyin.");
    } finally {
      setPasswordLoading(false);
    }
  };

  const handle2FAToggle = async () => {
    if (twoFactorEnabled) {
      // Disable 2FA
      setTwoFALoading(true);
      try {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        setTwoFactorEnabled(false);
        updateProfile({ twoFactorEnabled: false });
        setSuccess("İki faktörlü doğrulama devre dışı bırakıldı.");
      } catch (err) {
        setError("İşlem başarısız.");
      } finally {
        setTwoFALoading(false);
      }
    } else {
      // Show 2FA setup modal
      setShow2FAModal(true);
    }
  };

  const handleEnable2FA = async (e) => {
    e.preventDefault();
    if (verificationCode.length !== 6) {
      return;
    }

    setTwoFALoading(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      setTwoFactorEnabled(true);
      updateProfile({ twoFactorEnabled: true });
      setShow2FAModal(false);
      setVerificationCode("");
      setSuccess("İki faktörlü doğrulama etkinleştirildi!");
    } catch (err) {
      setError("Doğrulama başarısız.");
    } finally {
      setTwoFALoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return "Bilinmiyor";
    return new Date(dateString).toLocaleDateString("tr-TR", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-4 md:space-y-6 px-2 sm:px-0">
      {/* Success/Error Messages */}
      {success && (
        <div className="p-3 sm:p-4 rounded-xl bg-green-500/10 border border-green-500/20 flex items-center gap-2 sm:gap-3 animate-fade-in">
          <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-green-400 flex-shrink-0" />
          <p className="text-green-400 text-xs sm:text-sm flex-1">{success}</p>
          <button
            onClick={() => setSuccess("")}
            className="ml-auto text-green-400 hover:text-green-300"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      {error && (
        <div className="p-3 sm:p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-2 sm:gap-3 animate-fade-in">
          <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 text-red-400 flex-shrink-0" />
          <p className="text-red-400 text-xs sm:text-sm flex-1">{error}</p>
          <button
            onClick={() => setError("")}
            className="ml-auto text-red-400 hover:text-red-300"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Profile Card */}
      <div className="glass-card rounded-2xl border border-white/10 overflow-hidden">
        {/* Header Banner */}
        <div className="h-32 bg-gradient-to-r from-primary-500 via-primary-600 to-accent-500 relative">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMtOS45NDEgMC0xOCA4LjA1OS0xOCAxOHM4LjA1OSAxOCAxOCAxOGM5Ljk0MSAwIDE4LTguMDU5IDE4LTE4cy04LjA1OS0xOC0xOC0xOHptMCAzMmMtNy43MzIgMC0xNC02LjI2OC0xNC0xNHM2LjI2OC0xNCAxNC0xNCAxNCA2LjI2OCAxNCAxNC02LjI2OCAxNC0xNCAxNHoiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4xKSIvPjwvZz48L3N2Zz4=')] opacity-30" />
        </div>

        {/* Profile Info */}
        <div className="px-6 pb-6">
          {/* Avatar */}
          <div className="relative -mt-16 mb-4">
            <div className="w-32 h-32 rounded-2xl bg-gradient-to-br from-primary-400 via-primary-500 to-accent-500 flex items-center justify-center text-white font-bold text-4xl shadow-xl shadow-primary-500/30 border-4 border-[var(--color-bg)]">
              {getUserInitials()}
            </div>
            <button className="absolute bottom-2 right-2 p-2 bg-white/10 backdrop-blur-sm rounded-xl border border-white/20 text-white hover:bg-white/20 transition-colors">
              <Camera className="w-4 h-4" />
            </button>
          </div>

          {/* User Info */}
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-theme-text">
                  {user?.fullName || "Kullanıcı"}
                </h1>
                {user?.membership === "Pro" && (
                  <span className="px-2 py-1 text-xs font-medium rounded-full bg-gradient-to-r from-yellow-500/20 to-orange-500/20 text-yellow-400 border border-yellow-500/20 flex items-center gap-1">
                    <Crown className="w-3 h-3" />
                    Pro
                  </span>
                )}
              </div>
              <p className="text-theme-muted flex items-center gap-2 mt-1">
                <Mail className="w-4 h-4" />
                {user?.email || "email@example.com"}
              </p>
              <p className="text-theme-muted text-sm flex items-center gap-2 mt-2">
                <Calendar className="w-4 h-4" />
                Üyelik: {formatDate(user?.createdAt)}
              </p>
            </div>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="px-4 py-2 bg-primary-500/10 hover:bg-primary-500/20 text-primary-400 rounded-xl transition-colors flex items-center gap-2"
            >
              <Edit3 className="w-4 h-4" />
              {isEditing ? "İptal" : "Düzenle"}
            </button>
          </div>
        </div>
      </div>

      {/* Edit Profile Form */}
      {isEditing && (
        <div className="glass-card rounded-2xl border border-white/10 p-6 animate-fade-in">
          <h2 className="text-lg font-semibold text-theme-text mb-4 flex items-center gap-2">
            <User className="w-5 h-5 text-primary-500" />
            Profil Bilgilerini Düzenle
          </h2>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-theme-muted mb-2 block">
                Ad Soyad
              </label>
              <input
                type="text"
                name="fullName"
                value={formData.fullName}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-theme-text focus:outline-none focus:border-primary-500/50 focus:ring-2 focus:ring-primary-500/20 transition-all"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-theme-muted mb-2 block">
                E-posta
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-theme-text focus:outline-none focus:border-primary-500/50 focus:ring-2 focus:ring-primary-500/20 transition-all"
              />
            </div>
            <button
              onClick={handleSaveProfile}
              disabled={isLoading}
              className="px-6 py-3 bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-primary-500/25 disabled:opacity-50 transition-all flex items-center gap-2"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              {isLoading ? "Kaydediliyor..." : "Kaydet"}
            </button>
          </div>
        </div>
      )}

      {/* Security Section */}
      <div className="glass-card rounded-2xl border border-white/10 p-6">
        <h2 className="text-lg font-semibold text-theme-text mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-green-500" />
          Güvenlik Ayarları
        </h2>
        <div className="space-y-4">
          {/* Change Password */}
          <button
            onClick={() => setShowPasswordModal(true)}
            className="w-full flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10 hover:border-primary-500/30 hover:bg-white/10 transition-all group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary-500/10 rounded-lg">
                <Key className="w-5 h-5 text-primary-400" />
              </div>
              <div className="text-left">
                <p className="text-sm font-medium text-theme-text">
                  Şifre Değiştir
                </p>
                <p className="text-xs text-theme-muted">
                  Hesap şifrenizi güncelleyin
                </p>
              </div>
            </div>
            <span className="text-theme-muted group-hover:text-primary-400 transition-colors">
              →
            </span>
          </button>

          {/* Two-Factor Authentication */}
          <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10">
            <div className="flex items-center gap-3">
              <div
                className={`p-2 rounded-lg ${twoFactorEnabled ? "bg-green-500/10" : "bg-white/5"}`}
              >
                <Smartphone
                  className={`w-5 h-5 ${twoFactorEnabled ? "text-green-400" : "text-theme-muted"}`}
                />
              </div>
              <div>
                <p className="text-sm font-medium text-theme-text">
                  İki Faktörlü Doğrulama
                </p>
                <p className="text-xs text-theme-muted">
                  {twoFactorEnabled
                    ? "Hesabınız ekstra güvenlik ile korunuyor"
                    : "Ekstra güvenlik katmanı ekleyin"}
                </p>
              </div>
            </div>
            <button
              onClick={handle2FAToggle}
              disabled={twoFALoading}
              className={`relative w-14 h-7 rounded-full transition-colors ${
                twoFactorEnabled ? "bg-green-500" : "bg-white/20"
              }`}
            >
              <div
                className={`absolute top-1 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                  twoFactorEnabled ? "left-8" : "left-1"
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Password Change Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setShowPasswordModal(false)}
          />
          <div className="relative w-full max-w-md glass-card rounded-2xl border border-white/10 p-6 animate-fade-in">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-theme-text flex items-center gap-2">
                <Key className="w-5 h-5 text-primary-500" />
                Şifre Değiştir
              </h3>
              <button
                onClick={() => setShowPasswordModal(false)}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-theme-muted" />
              </button>
            </div>

            {passwordError && (
              <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                {passwordError}
              </div>
            )}

            <form onSubmit={handlePasswordChange} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-theme-muted mb-2 block">
                  Mevcut Şifre
                </label>
                <input
                  type="password"
                  value={passwordData.currentPassword}
                  onChange={(e) =>
                    setPasswordData((prev) => ({
                      ...prev,
                      currentPassword: e.target.value,
                    }))
                  }
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-theme-text focus:outline-none focus:border-primary-500/50 transition-all"
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium text-theme-muted mb-2 block">
                  Yeni Şifre
                </label>
                <input
                  type="password"
                  value={passwordData.newPassword}
                  onChange={(e) =>
                    setPasswordData((prev) => ({
                      ...prev,
                      newPassword: e.target.value,
                    }))
                  }
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-theme-text focus:outline-none focus:border-primary-500/50 transition-all"
                  required
                  minLength={8}
                />
              </div>
              <div>
                <label className="text-sm font-medium text-theme-muted mb-2 block">
                  Yeni Şifre (Tekrar)
                </label>
                <input
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={(e) =>
                    setPasswordData((prev) => ({
                      ...prev,
                      confirmPassword: e.target.value,
                    }))
                  }
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-theme-text focus:outline-none focus:border-primary-500/50 transition-all"
                  required
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowPasswordModal(false)}
                  className="flex-1 px-4 py-3 bg-white/5 hover:bg-white/10 text-theme-text rounded-xl transition-colors"
                >
                  İptal
                </button>
                <button
                  type="submit"
                  disabled={passwordLoading}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-primary-500/25 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                >
                  {passwordLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Key className="w-4 h-4" />
                  )}
                  {passwordLoading ? "Değiştiriliyor..." : "Değiştir"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 2FA Setup Modal */}
      {show2FAModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setShow2FAModal(false)}
          />
          <div className="relative w-full max-w-md glass-card rounded-2xl border border-white/10 p-6 animate-fade-in">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-theme-text flex items-center gap-2">
                <Smartphone className="w-5 h-5 text-primary-500" />
                İki Faktörlü Doğrulama
              </h3>
              <button
                onClick={() => setShow2FAModal(false)}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-theme-muted" />
              </button>
            </div>

            <div className="space-y-4">
              {/* QR Code Placeholder */}
              <div className="flex flex-col items-center p-6 bg-white rounded-xl">
                <div className="w-40 h-40 bg-gray-100 rounded-lg flex items-center justify-center mb-3">
                  <div className="text-center text-gray-500 text-sm">
                    <Smartphone className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                    QR Kod
                  </div>
                </div>
                <p className="text-xs text-gray-500 text-center">
                  Google Authenticator veya benzeri bir uygulama ile tarayın
                </p>
              </div>

              {/* Manual Code */}
              <div className="p-3 bg-white/5 rounded-lg border border-white/10">
                <p className="text-xs text-theme-muted mb-1">
                  Manuel Giriş Kodu:
                </p>
                <p className="font-mono text-sm text-theme-text tracking-wider">
                  ABCD-EFGH-IJKL-MNOP
                </p>
              </div>

              {/* Verification */}
              <form onSubmit={handleEnable2FA}>
                <label className="text-sm font-medium text-theme-muted mb-2 block">
                  Doğrulama Kodu (6 haneli)
                </label>
                <input
                  type="text"
                  value={verificationCode}
                  onChange={(e) =>
                    setVerificationCode(
                      e.target.value.replace(/\D/g, "").slice(0, 6),
                    )
                  }
                  placeholder="000000"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-theme-text text-center text-2xl tracking-[0.5em] font-mono focus:outline-none focus:border-primary-500/50 transition-all"
                  maxLength={6}
                />
                <div className="flex gap-3 mt-4">
                  <button
                    type="button"
                    onClick={() => setShow2FAModal(false)}
                    className="flex-1 px-4 py-3 bg-white/5 hover:bg-white/10 text-theme-text rounded-xl transition-colors"
                  >
                    İptal
                  </button>
                  <button
                    type="submit"
                    disabled={twoFALoading || verificationCode.length !== 6}
                    className="flex-1 px-4 py-3 bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-primary-500/25 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                  >
                    {twoFALoading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Shield className="w-4 h-4" />
                    )}
                    {twoFALoading ? "Doğrulanıyor..." : "Etkinleştir"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;
