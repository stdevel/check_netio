Name:           nagios-plugins-check_netio
Version:        1.0
Release:        1%{?dist}
Summary:        A Nagios / Icinga plugin for checking Koukaam NETIO devices

Group:          Applications/System
License:        GPL
URL:            https://github.com/stdevel/check_netio
Source0:        nagios-plugins-check_netio-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

#BuildRequires:
Requires:       python-requests

%description
This package contains a Nagios / Icinga plugin for checking port states and NTP synchronization of Koukaam NETIO PDU devices.

Check out the GitHub page for further information: https://github.com/stdevel/check_netio

%prep
%setup -q

%build
#change /usr/lib64 to /usr/lib if we're on i686
%ifarch i686
sed -i -e "s/usr\/lib64/usr\/lib/" check_netio.cfg
%endif

%install
install -m 0755 -d %{buildroot}%{_libdir}/nagios/plugins/
install -m 0755 check_netio.py %{buildroot}%{_libdir}/nagios/plugins/check_netio
%if 0%{?el7}
        install -m 0755 -d %{buildroot}%{_sysconfdir}/nrpe.d/
        install -m 0755 check_netio.cfg  %{buildroot}%{_sysconfdir}/nrpe.d/check_netio.cfg
%else
        install -m 0755 -d %{buildroot}%{_sysconfdir}/nagios/plugins.d/
        install -m 0755 check_netio.cfg  %{buildroot}%{_sysconfdir}/nagios/plugins.d/check_netio.cfg
%endif



%clean
rm -rf $RPM_BUILD_ROOT

%files
%if 0%{?el7}
        %config %{_sysconfdir}/nrpe.d/check_netio.cfg
%else
        %config %{_sysconfdir}/nagios/plugins.d/check_netio.cfg
%endif
%{_libdir}/nagios/plugins/check_netio


%changelog
* Sun Mar 08 2015 Christian Stankowic <info@stankowic-development.net> - 1.0.1
- First release
