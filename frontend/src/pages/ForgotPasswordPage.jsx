/**
 * Forgot Password Page - Password Reset Request
 * 🌙 Dark Mode | ✨ Glassmorphism | 🎨 Investia Brand
 */
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Mail,
  ArrowLeft,
  ArrowRight,
  AlertCircle,
  Loader2,
  CheckCircle,
} from "lucide-react";
import { validateEmail } from "../utils/validation";
import { authApi } from "../services/api";

const ForgotPasswordPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [fieldError, setFieldError] = useState("");

  const handleEmailChange = (e) => {
    setEmail(e.target.value);
    setError("");
    setFieldError("");
  };

  const handleBlur = () => {
    const result = validateEmail(email);
    if (!result.isValid) {
      setFieldError(result.errors[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate email
    const result = validateEmail(email);
    if (!result.isValid) {
      setFieldError(result.errors[0]);
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      // API call to request password reset
      // Not: Backend'de bu endpoint'i oluşturmanız gerekebilir
      // await authApi.forgotPassword(email);
      
      // Simüle edilmiş başarılı yanıt
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setSuccess(true);
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        err.message || 
        "Bir hata oluştu. Lütfen tekrar deneyin."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0f172a] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 -left-20 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-accent-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-radial from-primary-500/5 to-transparent" />

        <div
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: "50px 50px",
          }}
        />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-block">
            <svg
              width="180"
              height="54"
              viewBox="0 0 200 60"
              fill="none"
              className="mx-auto hover:scale-105 transition-transform duration-300"
            >
              <defs>
                <linearGradient
                  id="forgotLogoGradient"
                  x1="0%"
                  y1="0%"
                  x2="100%"
                  y2="0%"
                >
                  <stop offset="0%" stopColor="#10b981" />
                  <stop offset="100%" stopColor="#06b6d4" />
                </linearGradient>
              </defs>
              <path
                d="M5 45L20 30L30 40L55 15"
                stroke="url(#forgotLogoGradient)"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
              />
              <circle cx="20" cy="30" r="3" fill="#10b981" />
              <circle cx="30" cy="40" r="3" fill="#059669" />
              <circle cx="55" cy="15" r="3" fill="#06b6d4" />
              <text
                x="70"
                y="40"
                fontFamily="Inter, -apple-system, BlinkMacSystemFont, sans-serif"
                fontSize="26"
                fontWeight="800"
                fill="url(#forgotLogoGradient)"
              >
                Investia
              </text>
            </svg>
          </Link>
        </div>

        {/* Glass Card */}
        <div className="glass-card p-8 rounded-3xl border border-white/10 backdrop-blur-xl bg-white/5">
          {success ? (
            // Success State
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-green-500/20 flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-green-400" />
              </div>
              <h1 className="text-2xl font-bold text-white mb-2">
                E-posta Gönderildi!
              </h1>
              <p className="text-slate-400 text-sm mb-6">
                Şifre sıfırlama bağlantısı <span className="text-white font-medium">{email}</span> adresine gönderildi.
                Lütfen gelen kutunuzu kontrol edin.
              </p>
              <p className="text-slate-500 text-xs mb-6">
                E-posta gelmedi mi? Spam klasörünüzü kontrol edin veya birkaç dakika bekleyin.
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => setSuccess(false)}
                  className="w-full py-3 bg-white/5 border border-white/10 text-white rounded-xl hover:bg-white/10 transition-colors"
                >
                  Tekrar Dene
                </button>
                <Link
                  to="/login"
                  className="w-full py-3 bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-primary-500/25 transition-all flex items-center justify-center gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Giriş Sayfasına Dön
                </Link>
              </div>
            </div>
          ) : (
            // Form State
            <>
              <div className="text-center mb-8">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-primary-500/20 flex items-center justify-center">
                  <Mail className="w-8 h-8 text-primary-400" />
                </div>
                <h1 className="text-2xl font-bold text-white mb-2">
                  Şifremi Unuttum
                </h1>
                <p className="text-slate-400 text-sm">
                  E-posta adresinizi girin, şifre sıfırlama bağlantısı göndereceğiz.
                </p>
              </div>

              {/* Error Message */}
              {error && (
                <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-3">
                  <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                {/* Email Input */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-300">
                    E-posta Adresi
                  </label>
                  <div className="relative">
                    <Mail
                      className={`absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 ${
                        fieldError ? "text-red-400" : "text-slate-400"
                      }`}
                    />
                    <input
                      type="email"
                      value={email}
                      onChange={handleEmailChange}
                      onBlur={handleBlur}
                      placeholder="ornek@email.com"
                      className={`w-full pl-12 pr-4 py-3.5 bg-white/5 border rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 transition-all duration-200 ${
                        fieldError
                          ? "border-red-500/50 focus:border-red-500/50 focus:ring-red-500/20"
                          : "border-white/10 focus:border-primary-500/50 focus:ring-primary-500/20"
                      }`}
                      required
                    />
                  </div>
                  {fieldError && (
                    <p className="text-red-400 text-xs flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      {fieldError}
                    </p>
                  )}
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-4 bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-primary-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center justify-center gap-2 group"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Gönderiliyor...</span>
                    </>
                  ) : (
                    <>
                      <span>Sıfırlama Bağlantısı Gönder</span>
                      <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                </button>
              </form>

              {/* Back to Login */}
              <div className="mt-6 text-center">
                <Link
                  to="/login"
                  className="text-slate-400 hover:text-white transition-colors text-sm inline-flex items-center gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Giriş sayfasına dön
                </Link>
              </div>
            </>
          )}
        </div>

        {/* Help Text */}
        <p className="text-center text-slate-500 text-xs mt-6">
          Yardıma mı ihtiyacınız var?{" "}
          <a href="mailto:destek@investia.com" className="text-primary-400 hover:text-primary-300">
            Destek ekibiyle iletişime geçin
          </a>
        </p>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
